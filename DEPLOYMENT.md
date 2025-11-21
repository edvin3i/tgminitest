# Deployment Guide - Telegram Quiz NFT Platform

**Version:** 1.0
**Last Updated:** 2025-11-20
**Target Environments:** Production, Staging

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Infrastructure Setup](#infrastructure-setup)
3. [Environment Configuration](#environment-configuration)
4. [Database Setup](#database-setup)
5. [Deployment Steps](#deployment-steps)
6. [Post-Deployment Verification](#post-deployment-verification)
7. [Rollback Procedures](#rollback-procedures)
8. [Monitoring Setup](#monitoring-setup)
9. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Accounts & Services

- [x] GitHub account with repository access
- [x] Telegram Bot Token (from @BotFather)
- [x] TON wallet with mnemonic (mainnet for prod, testnet for staging)
- [x] Pinata account for IPFS storage
- [x] Sentry account for error tracking (optional but recommended)
- [x] Server/VPS with:
  - Ubuntu 22.04 LTS or newer
  - Minimum 2GB RAM
  - 20GB storage
  - Docker & Docker Compose installed
  - SSL certificate (Let's Encrypt recommended)

### Required Software

```bash
# On deployment server
- Docker Engine 24.0+
- Docker Compose 2.20+
- Git
- curl
- openssl
```

### Generate Required Secrets

```bash
# Generate SECRET_KEY
openssl rand -hex 32

# Generate WEBHOOK_SECRET
openssl rand -hex 32

# Generate strong passwords
openssl rand -base64 32
```

---

## Infrastructure Setup

### 1. Server Provisioning

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo apt install docker-compose-plugin

# Verify installation
docker --version
docker compose version
```

### 2. Firewall Configuration

```bash
# Allow SSH
sudo ufw allow 22/tcp

# Allow HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Allow PostgreSQL (only from localhost or specific IPs)
sudo ufw allow from 127.0.0.1 to any port 5432

# Enable firewall
sudo ufw enable
```

### 3. Create Application User

```bash
# Create dedicated user
sudo adduser --system --group --no-create-home tgquiz

# Create application directory
sudo mkdir -p /opt/tgquiz
sudo chown -R tgquiz:tgquiz /opt/tgquiz

# Create log directory
sudo mkdir -p /var/log/tgquiz
sudo chown -R tgquiz:tgquiz /var/log/tgquiz
```

---

## Environment Configuration

### 1. Clone Repository

```bash
cd /opt/tgquiz
git clone https://github.com/yourusername/tgminitest.git .
git checkout main  # or your release branch
```

### 2. Configure Production Environment

```bash
# Copy environment template
cp .env.production.example .env.production

# Edit with your values
nano .env.production
```

**Critical Settings to Update:**

```bash
# Production-specific
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO

# Database (use strong passwords!)
POSTGRES_PASSWORD=<generate-strong-password>
DATABASE_URL=postgresql+asyncpg://postgres:<password>@postgres:5432/tgquiznft_prod

# Redis
REDIS_PASSWORD=<generate-strong-password>

# Telegram
BOT_TOKEN=<your-production-bot-token>

# TON (MAINNET)
TON_API_KEY=<your-ton-api-key>
TON_NETWORK=mainnet
TON_WALLET_MNEMONIC=<your-24-word-mnemonic>
NFT_COLLECTION_ADDRESS=<your-mainnet-collection>

# IPFS
PINATA_API_KEY=<your-pinata-key>
PINATA_SECRET_KEY=<your-pinata-secret>

# Security
SECRET_KEY=<generated-secret-key>
WEBHOOK_SECRET=<generated-webhook-secret>

# Monitoring
SENTRY_DSN=<your-sentry-dsn>
```

### 3. Set Proper Permissions

```bash
# Secure environment file
chmod 600 .env.production
chown tgquiz:tgquiz .env.production
```

---

## Database Setup

### 1. Initialize Database

```bash
# Start only PostgreSQL first
docker compose -f docker-compose.prod.yml up -d postgres

# Wait for PostgreSQL to be ready
docker compose -f docker-compose.prod.yml exec postgres pg_isready

# Run migrations
docker compose -f docker-compose.prod.yml run --rm backend-api \
  alembic upgrade head
```

### 2. Create Admin User

```bash
# Connect to database
docker compose -f docker-compose.prod.yml exec postgres psql \
  -U postgres -d tgquiznft_prod

# Set admin user (replace with your Telegram ID)
UPDATE users SET is_admin = true WHERE telegram_id = YOUR_TELEGRAM_ID;

\q
```

### 3. Seed Initial Data (Optional)

```bash
# Only for staging or if you have seed data
docker compose -f docker-compose.prod.yml run --rm backend-api \
  python -m app.db.seed
```

---

## Deployment Steps

### Production Deployment

#### Step 1: Pull Latest Code

```bash
cd /opt/tgquiz
git pull origin main
```

#### Step 2: Build Docker Images

```bash
# Build production images
docker compose -f docker-compose.prod.yml build --no-cache

# Verify images
docker images | grep tgquiz
```

#### Step 3: Run Database Migrations

```bash
# Always run migrations before starting services
docker compose -f docker-compose.prod.yml run --rm backend-api \
  alembic upgrade head
```

#### Step 4: Start Services

```bash
# Start all services
docker compose -f docker-compose.prod.yml up -d

# Check status
docker compose -f docker-compose.prod.yml ps

# View logs
docker compose -f docker-compose.prod.yml logs -f
```

#### Step 5: Verify Deployment

```bash
# Check health endpoint
curl -f https://yourdomain.com/health

# Check API docs (if DEBUG=true in staging)
curl -f https://yourdomain.com/api/docs

# Check bot status
# Send /start to your bot
```

---

## Post-Deployment Verification

### Health Checks

```bash
# 1. API Health Check
curl -f https://yourdomain.com/health
# Expected: {"status":"healthy","database":"healthy","environment":"production"}

# 2. Database Connection
docker compose -f docker-compose.prod.yml exec backend-api \
  python -c "from app.db.database import check_db_connection; import asyncio; print(asyncio.run(check_db_connection()))"
# Expected: True

# 3. Redis Connection
docker compose -f docker-compose.prod.yml exec redis redis-cli ping
# Expected: PONG

# 4. Check Logs for Errors
docker compose -f docker-compose.prod.yml logs --tail=50 backend-api
docker compose -f docker-compose.prod.yml logs --tail=50 telegram-bot
```

### Functional Tests

1. **Bot Test:**
   - Send `/start` to bot
   - Try quiz flow
   - Test NFT minting

2. **API Test:**
   ```bash
   # List quizzes
   curl -X GET https://yourdomain.com/api/v1/quizzes/

   # Check specific quiz
   curl -X GET https://yourdomain.com/api/v1/quizzes/1
   ```

3. **Payment Test:**
   - Test TON payment flow
   - Verify webhook handling
   - Check NFT minting

---

## Rollback Procedures

### Quick Rollback to Previous Version

```bash
# 1. Stop current services
docker compose -f docker-compose.prod.yml down

# 2. Checkout previous version
git log --oneline -5  # Find commit to rollback to
git checkout <previous-commit-hash>

# 3. Rollback database (if needed)
docker compose -f docker-compose.prod.yml run --rm backend-api \
  alembic downgrade -1

# 4. Rebuild and restart
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d

# 5. Verify
curl -f https://yourdomain.com/health
```

### Emergency Stop

```bash
# Stop all services immediately
docker compose -f docker-compose.prod.yml down

# Stop but keep data
docker compose -f docker-compose.prod.yml stop

# Restart
docker compose -f docker-compose.prod.yml start
```

---

## Monitoring Setup

### 1. Sentry Integration

Already integrated in code. Just configure:

```bash
# In .env.production
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
SENTRY_ENVIRONMENT=production
SENTRY_TRACES_SAMPLE_RATE=0.1
```

### 2. Log Monitoring

```bash
# View live logs
docker compose -f docker-compose.prod.yml logs -f

# View specific service
docker compose -f docker-compose.prod.yml logs -f backend-api

# Search logs for errors
docker compose -f docker-compose.prod.yml logs backend-api | grep ERROR

# Export logs
docker compose -f docker-compose.prod.yml logs --no-color > deployment.log
```

### 3. Resource Monitoring

```bash
# Container stats
docker stats

# Disk usage
df -h
docker system df

# Database size
docker compose -f docker-compose.prod.yml exec postgres \
  psql -U postgres -d tgquiznft_prod -c "\l+"
```

### 4. Set Up Alerts

**Uptime Monitoring:**
- Use UptimeRobot or similar
- Monitor: https://yourdomain.com/health
- Alert on: Status not 200, response time > 5s

**Error Alerts:**
- Sentry automatic alerts
- Configure alert rules for critical errors

**Resource Alerts:**
- Disk usage > 80%
- Memory usage > 85%
- CPU usage > 90% for > 5 minutes

---

## Troubleshooting

### Database Connection Issues

```bash
# Check if PostgreSQL is running
docker compose -f docker-compose.prod.yml ps postgres

# Check PostgreSQL logs
docker compose -f docker-compose.prod.yml logs postgres

# Test connection
docker compose -f docker-compose.prod.yml exec postgres \
  psql -U postgres -d tgquiznft_prod -c "SELECT 1;"

# Restart PostgreSQL
docker compose -f docker-compose.prod.yml restart postgres
```

### Bot Not Responding

```bash
# Check bot logs
docker compose -f docker-compose.prod.yml logs telegram-bot

# Verify BOT_TOKEN
docker compose -f docker-compose.prod.yml exec telegram-bot \
  python -c "from app.config import settings; print(settings.BOT_TOKEN[:10])"

# Restart bot
docker compose -f docker-compose.prod.yml restart telegram-bot
```

### NFT Minting Failures

```bash
# Check TON service logs
docker compose -f docker-compose.prod.yml logs backend-api | grep TON

# Verify TON wallet
docker compose -f docker-compose.prod.yml exec backend-api \
  python -c "from app.services.ton.wallet_service import WalletService; import asyncio; ws = WalletService(); print(asyncio.run(ws.get_balance()))"

# Check IPFS connection
docker compose -f docker-compose.prod.yml logs backend-api | grep IPFS
```

### Performance Issues

```bash
# Check resource usage
docker stats

# Check slow queries
docker compose -f docker-compose.prod.yml exec postgres \
  psql -U postgres -d tgquiznft_prod -c "SELECT query, calls, total_time FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;"

# Restart services
docker compose -f docker-compose.prod.yml restart
```

---

## Maintenance Tasks

### Regular Tasks

**Daily:**
- Monitor error logs
- Check Sentry dashboard
- Verify backup completion

**Weekly:**
- Review resource usage
- Check for security updates
- Review slow queries

**Monthly:**
- Update dependencies
- Review and optimize database
- Test backup restoration
- Security audit

### Database Maintenance

```bash
# Vacuum database
docker compose -f docker-compose.prod.yml exec postgres \
  psql -U postgres -d tgquiznft_prod -c "VACUUM ANALYZE;"

# Check index health
docker compose -f docker-compose.prod.yml exec postgres \
  psql -U postgres -d tgquiznft_prod -c "SELECT schemaname, tablename, indexname, idx_scan FROM pg_stat_user_indexes WHERE idx_scan = 0;"

# Backup database
docker compose -f docker-compose.prod.yml exec postgres \
  pg_dump -U postgres tgquiznft_prod > backup_$(date +%Y%m%d).sql
```

---

## Security Checklist

- [ ] All .env files have 600 permissions
- [ ] Strong passwords for database and Redis
- [ ] Firewall configured correctly
- [ ] SSL certificates installed and auto-renewing
- [ ] Sentry DSN configured
- [ ] Regular backups enabled
- [ ] Admin Telegram IDs configured
- [ ] CORS origins restricted
- [ ] Debug mode disabled in production
- [ ] Secrets not committed to git
- [ ] Docker images from trusted sources
- [ ] Regular security updates applied

---

## Support & Resources

- **Project Repository:** https://github.com/yourusername/tgminitest
- **Documentation:** See PROJECT_STATE.md, QUICKSTART_NEXT_SESSION.md
- **Issue Tracker:** GitHub Issues
- **CI/CD:** GitHub Actions
- **Monitoring:** Sentry Dashboard

---

**Deployment completed successfully!** 🎉

Monitor logs for first 24 hours and verify all systems operational.
