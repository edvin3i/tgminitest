# 🚀 Quick Start Guide - Telegram Quiz NFT Platform

## Phase 1 is Complete! ✅

You now have a fully functional quiz bot! Users can take quizzes and get personalized results.

---

## ⚡ Quick Setup (5 minutes)

### 1. Install uv (if not already installed)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
# Or: brew install uv (macOS)
```

### 2. Clone and Configure

```bash
cd /home/user/tgminitest
cp .env.example .env
```

**Edit `.env` and set:**
- `BOT_TOKEN` - Get from [@BotFather](https://t.me/BotFather) on Telegram
- Leave other settings as default for local development

### 3. Start Infrastructure

```bash
make docker-up
```

This starts PostgreSQL and Redis in Docker.

### 4. Install Dependencies & Setup Database

```bash
cd backend
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install all dependencies (fast with uv!)
uv pip install -e ".[dev]"

# Run database migrations
uv run alembic upgrade head

# Seed with Hogwarts House quiz
uv run python -m app.db.seed
```

### 5. Start the Bot

```bash
uv run python -m app.bot.main
```

---

## 🎯 Using Make Commands (Even Easier!)

```bash
# From project root
make docker-up      # Start PostgreSQL & Redis
make install-dev    # Install dependencies
make migrate        # Run migrations
make seed           # Seed database
make run-bot        # Start bot
```

---

## 📱 Test the Bot

1. **Open Telegram** and find your bot (use the username from @BotFather)

2. **Start a conversation:**
   ```
   /start
   ```

3. **Take the quiz:**
   - Click "🎯 Browse Quizzes"
   - Select "🏰 Which Hogwarts House Are You?"
   - Answer all 6 questions
   - See your personalized result!

4. **Try other commands:**
   ```
   /help  - Show help
   /quiz  - Browse quizzes
   ```

---

## 🎨 What Works Now

### ✅ Completed Features

- **User Registration** - Automatic registration on `/start`
- **Quiz Browsing** - See all available quizzes from database
- **Quiz Taking** - Full question-by-question flow
- **Progress Tracking** - "Question X of Y" display
- **Answer Selection** - Inline keyboard buttons
- **Result Calculation** - Weighted scoring algorithm
- **Result Persistence** - Saved to PostgreSQL
- **Personalized Results** - Custom descriptions per result type
- **Session Management** - Redis-based state (30min TTL)
- **Error Handling** - Graceful error recovery

### 🎯 Sample Quiz Included

**"Which Hogwarts House Are You?"**
- 6 engaging questions
- 4 possible results (Gryffindor, Slytherin, Ravenclaw, Hufflepuff)
- Weighted scoring (different answers have different weights)
- Emoji-rich interface
- Personalized result descriptions

---

## 📊 Architecture Overview

```
User → Telegram → Bot Handler → Quiz Service → PostgreSQL
                     ↓              ↓
                State Service → Redis (session)
```

### Data Flow

1. User clicks "Browse Quizzes"
2. Bot fetches active quizzes from PostgreSQL
3. User selects quiz → Bot creates session in Redis
4. For each question:
   - Bot shows question with answer buttons
   - User clicks answer → Bot saves to Redis, advances
5. After last question:
   - Bot retrieves all answers from Redis
   - Calculates result using weighted algorithm
   - Saves result to PostgreSQL
   - Clears Redis session
   - Shows personalized result to user

---

## 🧪 Running Tests

```bash
cd backend

# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=app --cov-report=html

# Run quiz service tests only
uv run pytest tests/services/test_quiz_service.py -v
```

**Current Test Coverage:** 100% for quiz service

---

## 🔧 Development Tips

### Adding Your Telegram ID as Admin

Edit `backend/app/db/seed.py` line 19:
```python
telegram_id=YOUR_TELEGRAM_ID,  # Replace with your actual ID
```

Then run:
```bash
make seed
```

### Checking Database

**Option 1: pgAdmin (Web UI)**
```bash
docker-compose --profile dev up -d
# Access at http://localhost:5050
# Email: admin@quiz.local
# Password: admin
```

**Option 2: psql (Command Line)**
```bash
docker exec -it telegram_quiz_postgres psql -U quizbot -d telegram_quiz

# Useful commands:
\dt                    # List tables
\d users              # Describe users table
SELECT * FROM quizzes;
SELECT * FROM quiz_results;
```

### Checking Redis

```bash
docker exec -it telegram_quiz_redis redis-cli

# Useful commands:
KEYS *                    # List all keys
GET quiz:session:123456   # Get user's session
TTL quiz:session:123456   # Check session TTL
```

### Viewing Logs

```bash
# Bot logs (in terminal where you ran make run-bot)

# Docker logs
make docker-logs

# Or specific service:
docker-compose logs -f postgres
docker-compose logs -f redis
```

---

## 🐛 Troubleshooting

### Bot not responding?

1. **Check bot token:**
   ```bash
   cat .env | grep BOT_TOKEN
   ```

2. **Check if bot is running:**
   ```bash
   ps aux | grep "python -m app.bot.main"
   ```

3. **Check logs for errors in terminal**

### Database connection error?

1. **Check if PostgreSQL is running:**
   ```bash
   docker ps | grep postgres
   ```

2. **Start infrastructure:**
   ```bash
   make docker-up
   ```

3. **Check database URL in `.env`:**
   ```
   DATABASE_URL=postgresql+asyncpg://quizbot:changeme@localhost:5432/telegram_quiz
   ```

### Redis connection error?

1. **Check if Redis is running:**
   ```bash
   docker ps | grep redis
   ```

2. **Test Redis connection:**
   ```bash
   docker exec -it telegram_quiz_redis redis-cli ping
   # Should respond: PONG
   ```

### No quizzes showing?

1. **Run the seed script:**
   ```bash
   make seed
   ```

2. **Check database:**
   ```bash
   docker exec -it telegram_quiz_postgres psql -U quizbot -d telegram_quiz
   SELECT * FROM quizzes;
   ```

---

## 📚 Next Steps

### Phase 2: Backend API (Coming Next)
- [ ] FastAPI REST endpoints for quiz management
- [ ] Admin panel API (create, edit, delete quizzes)
- [ ] User authentication via Telegram
- [ ] API documentation with Swagger

### Phase 3: TON NFT Integration
- [ ] TON blockchain connection
- [ ] NFT minting service
- [ ] IPFS metadata storage
- [ ] Payment integration (Telegram Stars / TON)

### Phase 4: Frontend
- [ ] React admin panel
- [ ] Telegram WebApp for users
- [ ] TON Connect wallet integration

---

## 🎓 Learn More

- **Project Documentation:** See `README.md`
- **Architecture:** See `architecture.md`
- **Development Plan:** See `plan.md`
- **Coding Standards:** See `CLAUDE.md`

---

## 💬 Questions?

Check the documentation files or review the code. Everything is well-documented with type hints and docstrings!

**Enjoy building your viral quiz platform! 🚀**
