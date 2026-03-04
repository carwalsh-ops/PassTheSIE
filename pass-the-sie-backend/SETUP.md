# Pass The SIE - Backend Setup Guide

## Quick Start

### 1. Install Dependencies
```bash
cd pass-the-sie-backend
python3 -m venv venv
source venv/bin/activate  # On Mac
# venv\Scripts\activate  # On Windows

pip install -r requirements.txt
```

### 2. Configure Stripe
1. Go to https://dashboard.stripe.com/test/apikeys
2. Copy your test secret key
3. Replace `sk_test_YOUR_STRIPE_KEY` in main.py with your key

### 3. Run Server
```bash
uvicorn main:app --reload
```

Server runs at: http://localhost:8000

### 4. Test API
```bash
# Register a user
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"test","email":"test@test.com","password":"password123"}'

# Get questions
curl http://localhost:8000/api/questions

# Get leaderboard
curl http://localhost:8000/api/users/leaderboard
```

## Deployment

### Render (Free)
1. Push code to GitHub
2. Connect GitHub to Render
3. Set build command: `pip install -r requirements.txt`
4. Set start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`

### Stripe Setup
1. Create product: https://dashboard.stripe.com/test/products
2. Get price ID (starts with `price_`)
3. Update `price_id` in the checkout endpoint

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/auth/register | Create account |
| POST | /api/auth/login | Login |
| GET | /api/users/progress | Get user stats |
| PUT | /api/users/progress | Update progress |
| GET | /api/users/leaderboard | Top users |
| GET | /api/questions | Get quiz questions |
| POST | /api/subscriptions/create-checkout | Start subscription |
| GET | /api/subscriptions/status | Check subscription |

## Frontend Connection

Update your frontend to call these API endpoints instead of localStorage.

Example:
```javascript
// Instead of localStorage
const response = await fetch('https://your-backend.onrender.com/api/users/progress?user_id=1');
const data = await response.json();
```
