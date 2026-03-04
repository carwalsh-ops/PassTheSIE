# Pass The SIE - Backend

## Setup
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install fastapi uvicorn sqlalchemy pydantic python-jose passlib bcrypt stripe

# Run server
uvicorn main:app --reload
```

## Environment Variables
```
SECRET_KEY=your-secret-key
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
DATABASE_URL=sqlite:///./passthesie.db
```

## API Endpoints

### Auth
- POST /api/auth/register
- POST /api/auth/login
- GET /api/auth/me

### Users
- GET /api/users/stats
- PUT /api/users/progress
- GET /api/users/leaderboard

### Subscriptions
- POST /api/subscriptions/create-checkout
- POST /api/subscriptions/webhook
- GET /api/subscriptions/status

### Questions
- GET /api/questions (with category filter)
- GET /api/questions/random

## Database Schema

### Users
- id, username, email, password_hash
- is_pro, stripe_customer_id
- created_at

### Progress
- user_id, questions_answered, correct_answers
- best_streak, current_streak
- category_scores (JSON)

### Subscriptions
- user_id, stripe_subscription_id
- status, current_period_end
