"""
Pass The SIE - Backend API
FastAPI application with SQLite database
"""

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta
import sqlite3
import hashlib
import secrets
import stripe
from datetime import datetime

# Initialize FastAPI
app = FastAPI(title="Pass The SIE API")

# CORS - allow all origins for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Stripe - SET YOUR KEY HERE
stripe.api_key = "sk_test_YOUR_STRIPE_KEY"

# Database setup
DATABASE = "passthesie.db"

def init_db():
    """Initialize database tables"""
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    
    # Users table
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            is_pro INTEGER DEFAULT 0,
            stripe_customer_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Progress table
    c.execute("""
        CREATE TABLE IF NOT EXISTS progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            questions_answered INTEGER DEFAULT 0,
            correct_answers INTEGER DEFAULT 0,
            best_streak INTEGER DEFAULT 0,
            category_scores TEXT DEFAULT '{}',
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    
    # Subscriptions table
    c.execute("""
        CREATE TABLE IF NOT EXISTS subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            stripe_subscription_id TEXT,
            status TEXT DEFAULT 'inactive',
            current_period_end TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    
    conn.commit()
    conn.close()

# Initialize on startup
init_db()

# Pydantic models
class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    is_pro: bool
    created_at: str

class ProgressResponse(BaseModel):
    questions_answered: int
    correct_answers: int
    best_streak: int
    accuracy: float

class LeaderboardEntry(BaseModel):
    username: str
    questions_answered: int
    accuracy: float
    level: int

# Helper functions
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, password_hash: str) -> bool:
    return hash_password(password) == password_hash

def generate_token() -> str:
    return secrets.token_urlsafe(32)

# Auth endpoints
@app.post("/api/auth/register")
def register(user: UserCreate):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    
    # Check if username exists
    c.execute("SELECT id FROM users WHERE username = ?", (user.username,))
    if c.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="Username already exists")
    
    # Check if email exists
    c.execute("SELECT id FROM users WHERE email = ?", (user.email,))
    if c.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="Email already exists")
    
    # Create user
    password_hash = hash_password(user.password)
    c.execute(
        "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
        (user.username, user.email, password_hash)
    )
    user_id = c.lastrowid
    
    # Create progress entry
    c.execute("INSERT INTO progress (user_id) VALUES (?)", (user_id,))
    
    conn.commit()
    conn.close()
    
    return {"message": "User created successfully", "user_id": user_id}

@app.post("/api/auth/login")
def login(user: UserLogin):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    
    c.execute(
        "SELECT id, username, email, password_hash, is_pro FROM users WHERE username = ?",
        (user.username,)
    )
    row = c.fetchone()
    conn.close()
    
    if not row:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not verify_password(user.password, row[3]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Generate simple token (in production, use JWT)
    token = generate_token()
    
    return {
        "token": token,
        "user": {
            "id": row[0],
            "username": row[1],
            "email": row[2],
            "is_pro": bool(row[4])
        }
    }

# Get current user
@app.get("/api/auth/me")
def get_me(token: str = None):
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # In production, decode JWT token
    # For now, return demo user
    return {
        "id": 1,
        "username": "demo_user",
        "email": "demo@example.com",
        "is_pro": False
    }

# Progress endpoints
@app.get("/api/users/progress")
def get_progress(user_id: int = 1):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    
    c.execute("""
        SELECT questions_answered, correct_answers, best_streak, category_scores
        FROM progress WHERE user_id = ?
    """, (user_id,))
    row = c.fetchone()
    conn.close()
    
    if not row:
        return {
            "questions_answered": 0,
            "correct_answers": 0,
            "best_streak": 0,
            "accuracy": 0,
            "level": 1
        }
    
    questions_answered = row[0]
    correct_answers = row[1]
    accuracy = (correct_answers / questions_answered * 100) if questions_answered > 0 else 0
    level = (questions_answered // 5) + 1
    
    return {
        "questions_answered": questions_answered,
        "correct_answers": correct_answers,
        "best_streak": row[2],
        "accuracy": round(accuracy, 1),
        "level": level
    }

@app.put("/api/users/progress")
def update_progress(
    correct: bool,
    user_id: int = 1
):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    
    # Get current progress
    c.execute("""
        SELECT questions_answered, correct_answers, best_streak
        FROM progress WHERE user_id = ?
    """, (user_id,))
    row = c.fetchone()
    
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Progress not found")
    
    questions_answered = row[0] + 1
    correct_answers = row[1] + (1 if correct else 0)
    best_streak = row[2]
    
    # Update progress
    c.execute("""
        UPDATE progress
        SET questions_answered = ?, correct_answers = ?, last_updated = CURRENT_TIMESTAMP
        WHERE user_id = ?
    """, (questions_answered, correct_answers, user_id))
    
    conn.commit()
    conn.close()
    
    level = (questions_answered // 5) + 1
    
    return {
        "questions_answered": questions_answered,
        "correct_answers": correct_answers,
        "level": level
    }

# Leaderboard
@app.get("/api/users/leaderboard")
def get_leaderboard(limit: int = 10):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    
    c.execute("""
        SELECT u.username, p.questions_answered, p.correct_answers
        FROM users u
        JOIN progress p ON u.id = p.user_id
        ORDER BY p.questions_answered DESC
        LIMIT ?
    """, (limit,))
    
    rows = c.fetchall()
    conn.close()
    
    leaderboard = []
    for i, row in enumerate(rows):
        accuracy = (row[2] / row[1] * 100) if row[1] > 0 else 0
        leaderboard.append({
            "rank": i + 1,
            "username": row[0],
            "questions_answered": row[1],
            "accuracy": round(accuracy, 1),
            "level": (row[1] // 5) + 1
        })
    
    return leaderboard

# Admin endpoint - list all users
@app.get("/api/admin/users")
def get_all_users():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    
    c.execute("""
        SELECT u.id, u.username, u.email, u.is_pro, u.created_at, 
               p.questions_answered, p.correct_answers, p.best_streak
        FROM users u
        LEFT JOIN progress p ON u.id = p.user_id
        ORDER BY u.created_at DESC
    """)
    
    rows = c.fetchall()
    conn.close()
    
    users = []
    for row in rows:
        users.append({
            "id": row[0],
            "username": row[1],
            "email": row[2],
            "is_pro": bool(row[3]),
            "created_at": row[4],
            "questions_answered": row[5] or 0,
            "correct_answers": row[6] or 0,
            "best_streak": row[7] or 0
        })
    
    return {"users": users, "total": len(users)}

# Stripe subscription endpoints
@app.post("/api/subscriptions/create-checkout")
def create_checkout_session(user_id: int = 1, price_id: str = "price_pro_monthly"):
    """Create a Stripe checkout session"""
    try:
        checkout_session = stripe.checkout.Session.create(
            customer_email="user@example.com",  # In production, get from user
            payment_method_types=["card"],
            line_items=[
                {
                    "price": price_id,
                    "quantity": 1,
                },
            ],
            mode="subscription",
            success_url="https://passthesie.com/success?session_id={CHECKOUT_SESSION_ID}",
            cancel_url="https://passthesie.com/cancel",
            metadata={"user_id": user_id}
        )
        return {"url": checkout_session.url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/subscriptions/webhook")
def stripe_webhook(payload: bytes, signature: str):
    """Handle Stripe webhooks"""
    # In production, verify webhook signature
    # For now, just acknowledge
    return {"status": "received"}

@app.get("/api/subscriptions/status")
def get_subscription_status(user_id: int = 1):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    
    c.execute("""
        SELECT status, current_period_end
        FROM subscriptions WHERE user_id = ?
        ORDER BY created_at DESC LIMIT 1
    """, (user_id,))
    row = c.fetchone()
    conn.close()
    
    if row:
        return {
            "status": row[0],
            "current_period_end": row[1]
        }
    
    return {"status": "inactive", "current_period_end": None}

# Questions endpoint
@app.get("/api/questions")
def get_questions(
    category: str = None,
    limit: int = 10
):
    """Return quiz questions"""
    # This would come from database in production
    # For now, return a subset of questions
    questions = [
        {
            "id": 1,
            "category": "Options",
            "question": "What is the maximum loss for buying a call option?",
            "options": ["Unlimited", "The premium paid", "Strike price minus premium", "Stock price minus strike"],
            "correct": 1,
            "explanation": "Call buyers risk only the premium paid."
        },
        {
            "id": 2,
            "category": "Suitability",
            "question": "Before recommending a securities transaction, a broker must obtain:",
            "options": ["Favorite sports team", "Investment objectives, risk tolerance, and financial situation", "Political affiliation", "Social media activity"],
            "correct": 1,
            "explanation": "KYC rule requires knowing customer's objectives, risk tolerance, and financial situation."
        },
        {
            "id": 3,
            "category": "Regulation",
            "question": "What is the purpose of FINRA's Rule 2111?",
            "options": ["Prevent fraud", "Ensure recommendations are suitable", "Protect customer assets", "Enforce licensing"],
            "correct": 1,
            "explanation": "Rule 2111 requires reasonable grounds for believing recommendations are suitable."
        },
        {
            "id": 4,
            "category": "Economics",
            "question": "If the Fed increases the discount rate, what happens?",
            "options": ["Increased inflation", "Decreased borrowing", "Higher unemployment", "Lower GDP growth"],
            "correct": 1,
            "explanation": "Higher discount rate = higher borrowing costs = less borrowing."
        },
        {
            "id": 5,
            "category": "Client Accounts",
            "question": "Which account has the highest contribution limits?",
            "options": ["Traditional IRA", "Roth IRA", "401(k)", "HSA"],
            "correct": 2,
            "explanation": "401(k) limits are highest ($23,000 in 2024)."
        }
    ]
    
    if category:
        questions = [q for q in questions if q["category"].lower() == category.lower()]
    
    return questions[:limit]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
