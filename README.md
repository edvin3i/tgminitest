# 🎯 Telegram Quiz NFT Platform

A viral Telegram mini-app where users take personality quizzes and mint unique NFTs on the TON blockchain.

## 🚀 Features

- 🎮 Interactive personality quizzes in Telegram
- 🎨 Mint quiz results as NFTs on TON blockchain
- 📊 User statistics and NFT gallery
- 👨‍💼 Admin panel for quiz management
- 🔐 Secure authentication via Telegram
- ⚡ Fast and scalable architecture

## ⚡ Quick Start

```bash
# Install uv (if not installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone and setup
git clone <repository-url>
cd tgminitest
cp .env.example .env  # Edit with your BOT_TOKEN

# Start infrastructure
make docker-up

# Install dependencies and run
cd backend
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"
uv run alembic upgrade head
uv run python -m app.bot.main
```

Or use Make commands:
```bash
make install-dev    # Install dependencies
make docker-up      # Start PostgreSQL & Redis
make migrate        # Run migrations
make run-bot        # Start bot
```

## 🏗️ Architecture

- **Backend**: Python 3.12, FastAPI, Aiogram 3
- **Package Manager**: uv (10-100x faster than pip!)
- **Database**: PostgreSQL 17, Redis 8
- **Blockchain**: TON (The Open Network)
- **Frontend**: React 18 + TypeScript (Phase 4)

## 📋 Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) - Fast Python package installer (recommended)
- Docker & Docker Compose
- PostgreSQL 17
- Redis 8
- Telegram Bot Token (from @BotFather)

## 🛠️ Installation & Setup

### 1. Clone the repository

```bash
git clone <repository-url>
cd tgminitest
```

### 2. Set up environment variables

```bash
cp .env.example .env
```

Edit `.env` and fill in your values:
- `BOT_TOKEN`: Get from @BotFather on Telegram
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `SECRET_KEY`: Generate with `openssl rand -hex 32`

### 3. Start infrastructure with Docker

```bash
docker-compose up -d
```

This will start:
- PostgreSQL on port 5432
- Redis on port 6379
- pgAdmin on port 5050 (optional, use `--profile dev`)

### 4. Install Python dependencies

We use **[uv](https://docs.astral.sh/uv/)** - an extremely fast Python package installer and resolver written in Rust.

#### Option A: Using uv (Recommended - 10-100x faster!)

```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh
# Or on macOS: brew install uv
# Or on Windows: powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Navigate to backend
cd backend

# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install all dependencies (production + dev)
uv pip install -e ".[dev]"

# Or install only production dependencies
uv pip install -e .
```

#### Option B: Using pip (Traditional method)

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

> **Why uv?** It's 10-100x faster than pip, has better dependency resolution, and is maintained by the Astral team (creators of Ruff). Perfect for modern Python projects!

### 5. Run database migrations

```bash
# Create initial migration
alembic revision --autogenerate -m "Initial schema"

# Apply migrations
alembic upgrade head
```

### 6. Run the bot

```bash
python -m app.bot.main
```

### 7. Run the API (optional)

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 🧪 Running Tests

```bash
cd backend

# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=app --cov-report=html

# Run specific test file
uv run pytest tests/services/test_user_service.py -v

# Run with markers
uv run pytest -m unit
uv run pytest -m integration
```

> **Tip:** Use `uv run` to automatically run commands in your virtual environment without activating it!

## 📝 Code Quality

```bash
# Format code
uv run black .
uv run ruff format .

# Lint code
uv run ruff check .

# Type checking
uv run mypy app/
```

## 🔧 Development with uv

```bash
# Add a new dependency
uv pip install <package-name>

# Add a dev dependency
uv pip install <package-name> --group dev

# Update all dependencies
uv pip install --upgrade -e ".[dev]"

# Sync dependencies with pyproject.toml
uv pip sync

# Run any command without activating venv
uv run <command>

# Example: Run bot without activation
uv run python -m app.bot.main
```

## 📚 Project Structure

```
telegram-quiz-nft/
├── backend/
│   ├── app/
│   │   ├── api/              # API endpoints
│   │   ├── bot/              # Telegram bot
│   │   ├── db/               # Database connection
│   │   ├── models/           # SQLAlchemy models
│   │   ├── schemas/          # Pydantic schemas
│   │   ├── services/         # Business logic
│   │   ├── config.py         # Configuration
│   │   └── main.py           # FastAPI app
│   ├── tests/                # Tests
│   ├── alembic/              # Database migrations
│   ├── requirements.txt      # Dependencies
│   ├── pyproject.toml        # Project config
│   └── Dockerfile
├── frontend/                 # React app (Phase 4)
├── docs/                     # Documentation
├── docker-compose.yml
├── .env.example
├── CLAUDE.md                 # AI coding standards
├── architecture.md           # System architecture
├── plan.md                   # Development plan
├── todo.md                   # Task tracker
└── README.md
```

## 🎯 Development Roadmap

### ✅ Phase 1: Foundation & MVP Bot (Current)
- [x] Project setup
- [x] Database models
- [x] Basic bot handlers
- [x] User registration
- [ ] Quiz flow implementation
- [ ] Result calculation

### 🔄 Phase 2: Backend API
- [ ] FastAPI endpoints
- [ ] Authentication
- [ ] Quiz CRUD
- [ ] Admin panel API

### 🔜 Phase 3: TON Blockchain Integration
- [ ] TON SDK integration
- [ ] NFT minting service
- [ ] Payment processing
- [ ] Metadata storage (IPFS)

### 🔜 Phase 4: Frontend
- [ ] Admin panel (React)
- [ ] Telegram WebApp
- [ ] TON Connect wallet

## 📖 Documentation

- [Architecture](./architecture.md) - System architecture and design
- [Plan](./plan.md) - Detailed development plan
- [Todo](./todo.md) - Current tasks and progress
- [CLAUDE.md](./CLAUDE.md) - AI assistant coding standards

## 🤝 Contributing

1. Follow the coding standards in [CLAUDE.md](./CLAUDE.md)
2. Write tests for all new features
3. Run linting and type checking before committing
4. Create meaningful commit messages

## 📄 License

[License Type] - See LICENSE file for details

## 🙋 Support

For questions or issues:
- Open an issue on GitHub
- Contact the development team

---

**Built with ❤️ using Python, FastAPI, Aiogram, and TON**
