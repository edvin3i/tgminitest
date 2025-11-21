# Operations Runbook - Telegram Quiz NFT Platform

**Purpose:** Quick reference for common operations, incidents, and emergency procedures
**Audience:** DevOps engineers, on-call engineers, system administrators

---

## Quick Reference

### Essential Commands

```bash
# View all services status
docker compose -f docker-compose.prod.yml ps

# View logs (all services)
docker compose -f docker-compose.prod.yml logs -f --tail=100

# Restart specific service
docker compose -f docker-compose.prod.yml restart backend-api

# Stop all services
docker compose -f docker-compose.prod.yml down

# Start all services
docker compose -f docker-compose.prod.yml up -d
```

### Key URLs

- **API Health:** https://yourdomain.com/health
- **API Docs:** https://yourdomain.com/api/docs (staging only)
- **Sentry Dashboard:** https://sentry.io/organizations/your-org/projects/tgquiz/
- **GitHub Actions:** https://github.com/yourusername/tgminitest/actions

---

## Incident Response Procedures

### 🚨 Severity Levels

- **P0 (Critical):** Complete service outage, data loss, security breach
- **P1 (High):** Major feature broken, significant user impact
- **P2 (Medium):** Minor feature broken, some users affected
- **P3 (Low):** Cosmetic issues, no user impact

---

## P0: Complete Service Outage

### Symptoms
- Health endpoint returns 5XX
- Bot not responding
- Users reporting complete inability to use service

### Immediate Actions

```bash
# 1. Acknowledge incident
# Post in incident channel: "P0 incident acknowledged, investigating"

# 2. Check all services
docker compose -f docker-compose.prod.yml ps

# 3. Check logs for errors
docker compose -f docker-compose.prod.yml logs --tail=200 | grep ERROR

# 4. Verify external dependencies
curl -f https://yourdomain.com/health  # API
curl -f https://api.telegram.org/  # Telegram
# Check TON network status: https://toncenter.com/api/v2/getStatus

# 5. Quick restart (if no obvious cause)
docker compose -f docker-compose.prod.yml restart

# 6. If restart doesn't help, rollback
git log --oneline -5
git checkout <previous-working-commit>
docker compose -f docker-compose.prod.yml up -d --build
```

### Investigation

```bash
# Check system resources
df -h  # Disk space
free -h  # Memory
top  # CPU usage

# Check Docker resources
docker stats

# Check PostgreSQL
docker compose -f docker-compose.prod.yml exec postgres \
  psql -U postgres -d tgquiznft_prod -c "SELECT count(*) FROM users;"

# Check Redis
docker compose -f docker-compose.prod.yml exec redis redis-cli ping
```

### Resolution Steps

1. Identify root cause
2. Apply fix or rollback
3. Verify service restoration
4. Post-incident review within 24 hours

---

## P1: Database Connection Failures

### Symptoms
```
ERROR: Connection to database failed
sqlalchemy.exc.OperationalError
```

### Diagnosis

```bash
# 1. Check if PostgreSQL is running
docker compose -f docker-compose.prod.yml ps postgres

# 2. Check PostgreSQL logs
docker compose -f docker-compose.prod.yml logs postgres --tail=100

# 3. Check connection pool
docker compose -f docker-compose.prod.yml logs backend-api | grep "pool"

# 4. Check database connections
docker compose -f docker-compose.prod.yml exec postgres \
  psql -U postgres -d tgquiznft_prod -c "SELECT count(*) FROM pg_stat_activity;"
```

### Resolution

```bash
# Option 1: Restart PostgreSQL
docker compose -f docker-compose.prod.yml restart postgres

# Option 2: If connections exhausted, restart backend
docker compose -f docker-compose.prod.yml restart backend-api telegram-bot

# Option 3: If corruption suspected, restore from backup
# See "Database Restore" section below
```

---

## P1: Bot Not Responding to Commands

### Symptoms
- Users report bot not responding
- /start command times out

### Diagnosis

```bash
# 1. Check bot service status
docker compose -f docker-compose.prod.yml ps telegram-bot

# 2. Check bot logs
docker compose -f docker-compose.prod.yml logs telegram-bot --tail=100

# 3. Test Telegram API
curl https://api.telegram.org/bot<BOT_TOKEN>/getMe

# 4. Check bot webhook (if using webhooks)
curl https://api.telegram.org/bot<BOT_TOKEN>/getWebhookInfo
```

### Resolution

```bash
# Option 1: Restart bot
docker compose -f docker-compose.prod.yml restart telegram-bot

# Option 2: If token issues
# Verify BOT_TOKEN in .env.production
grep BOT_TOKEN .env.production

# Option 3: Clear webhook (if using polling)
curl -X POST https://api.telegram.org/bot<BOT_TOKEN>/deleteWebhook

# Restart bot after fixing
docker compose -f docker-compose.prod.yml restart telegram-bot
```

---

## P1: NFT Minting Failures

### Symptoms
```
ERROR: NFT minting failed
ERROR: TON transaction failed
ERROR: IPFS upload failed
```

### Diagnosis

```bash
# 1. Check backend logs
docker compose -f docker-compose.prod.yml logs backend-api | grep -i "nft\|ton\|ipfs"

# 2. Check TON wallet balance
docker compose -f docker-compose.prod.yml exec backend-api \
  python -c "
from app.services.ton.wallet_service import WalletService
import asyncio
ws = WalletService()
print(asyncio.run(ws.get_balance()))
"

# 3. Check IPFS connectivity
docker compose -f docker-compose.prod.yml exec backend-api \
  curl -f https://api.pinata.cloud/data/testAuthentication \
  -H "pinata_api_key: $PINATA_API_KEY" \
  -H "pinata_secret_api_key: $PINATA_SECRET_KEY"

# 4. Check pending mint transactions
docker compose -f docker-compose.prod.yml exec postgres \
  psql -U postgres -d tgquiznft_prod -c \
  "SELECT id, status, created_at FROM mint_transactions WHERE status = 'pending' ORDER BY created_at DESC LIMIT 10;"
```

### Resolution

```bash
# If wallet balance low:
# 1. Top up TON wallet
# 2. Verify balance increased

# If IPFS issues:
# 1. Verify Pinata API keys
# 2. Check Pinata dashboard for quota limits
# 3. Consider temporary file storage fallback

# If TON network issues:
# 1. Check TON network status
# 2. Retry failed transactions
docker compose -f docker-compose.prod.yml exec backend-api \
  python -m app.services.ton.retry_failed_mints

# Clean up stuck transactions
docker compose -f docker-compose.prod.yml exec postgres \
  psql -U postgres -d tgquiznft_prod -c \
  "UPDATE mint_transactions SET status = 'failed' WHERE status = 'pending' AND created_at < NOW() - INTERVAL '1 hour';"
```

---

## P2: High Memory Usage

### Symptoms
```
WARNING: Memory usage above 85%
docker stats shows high memory consumption
```

### Diagnosis

```bash
# 1. Check container memory usage
docker stats --no-stream

# 2. Check system memory
free -h

# 3. Check for memory leaks in logs
docker compose -f docker-compose.prod.yml logs backend-api | grep -i "memory\|leak"

# 4. Check database cache
docker compose -f docker-compose.prod.yml exec postgres \
  psql -U postgres -d tgquiznft_prod -c \
  "SELECT pg_size_pretty(pg_database_size('tgquiznft_prod'));"
```

### Resolution

```bash
# Option 1: Restart services (immediate relief)
docker compose -f docker-compose.prod.yml restart backend-api

# Option 2: Clear Redis cache
docker compose -f docker-compose.prod.yml exec redis redis-cli FLUSHDB

# Option 3: Vacuum database
docker compose -f docker-compose.prod.yml exec postgres \
  psql -U postgres -d tgquiznft_prod -c "VACUUM FULL;"

# Option 4: Increase container memory limits
# Edit docker-compose.prod.yml, add:
# deploy:
#   resources:
#     limits:
#       memory: 2G
docker compose -f docker-compose.prod.yml up -d --force-recreate
```

---

## P2: Slow Database Queries

### Symptoms
```
WARNING: Query took 5s to complete
Users reporting slow quiz loading
```

### Diagnosis

```bash
# 1. Find slow queries
docker compose -f docker-compose.prod.yml exec postgres \
  psql -U postgres -d tgquiznft_prod -c \
  "SELECT query, calls, total_time, mean_time FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;"

# 2. Check missing indexes
docker compose -f docker-compose.prod.yml exec postgres \
  psql -U postgres -d tgquiznft_prod -c \
  "SELECT schemaname, tablename, attname FROM pg_stats WHERE null_frac > 0.5;"

# 3. Check table sizes
docker compose -f docker-compose.prod.yml exec postgres \
  psql -U postgres -d tgquiznft_prod -c \
  "SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) FROM pg_tables WHERE schemaname = 'public' ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;"
```

### Resolution

```bash
# 1. Analyze and vacuum
docker compose -f docker-compose.prod.yml exec postgres \
  psql -U postgres -d tgquiznft_prod -c "VACUUM ANALYZE;"

# 2. Add missing indexes (example)
docker compose -f docker-compose.prod.yml exec postgres \
  psql -U postgres -d tgquiznft_prod -c \
  "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_quiz_results_user_id ON quiz_results(user_id);"

# 3. Restart PostgreSQL to clear cache
docker compose -f docker-compose.prod.yml restart postgres
```

---

## Routine Operations

### Deploy New Version

```bash
# 1. Backup database first
./scripts/backup_database.sh

# 2. Pull latest code
cd /opt/tgquiz
git fetch origin
git checkout main
git pull origin main

# 3. Run migrations
docker compose -f docker-compose.prod.yml run --rm backend-api \
  alembic upgrade head

# 4. Build and deploy
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d

# 5. Verify deployment
curl -f https://yourdomain.com/health

# 6. Monitor logs for 10 minutes
docker compose -f docker-compose.prod.yml logs -f
```

### Database Backup

```bash
# Manual backup
docker compose -f docker-compose.prod.yml exec postgres \
  pg_dump -U postgres -Fc tgquiznft_prod > backup_$(date +%Y%m%d_%H%M%S).dump

# Verify backup
ls -lh backup_*.dump

# Upload to S3 (if configured)
aws s3 cp backup_*.dump s3://your-backup-bucket/postgres/
```

### Database Restore

```bash
# 1. Stop services
docker compose -f docker-compose.prod.yml stop backend-api telegram-bot

# 2. Drop and recreate database
docker compose -f docker-compose.prod.yml exec postgres \
  psql -U postgres -c "DROP DATABASE IF EXISTS tgquiznft_prod;"
docker compose -f docker-compose.prod.yml exec postgres \
  psql -U postgres -c "CREATE DATABASE tgquiznft_prod;"

# 3. Restore from backup
docker compose -f docker-compose.prod.yml exec -T postgres \
  pg_restore -U postgres -d tgquiznft_prod < backup_20250120_143000.dump

# 4. Restart services
docker compose -f docker-compose.prod.yml start backend-api telegram-bot

# 5. Verify
curl -f https://yourdomain.com/health
```

### View Active Users

```bash
docker compose -f docker-compose.prod.yml exec postgres \
  psql -U postgres -d tgquiznft_prod -c \
  "SELECT COUNT(DISTINCT user_id) as active_users_7d FROM quiz_results WHERE completed_at > NOW() - INTERVAL '7 days';"
```

### View Quiz Statistics

```bash
docker compose -f docker-compose.prod.yml exec postgres \
  psql -U postgres -d tgquiznft_prod -c \
  "SELECT
    COUNT(*) as total_completions,
    COUNT(DISTINCT user_id) as unique_users,
    AVG(score) as avg_score,
    COUNT(CASE WHEN nft_minted THEN 1 END) as nfts_minted
   FROM quiz_results;"
```

### Clear Redis Cache

```bash
# Clear specific pattern
docker compose -f docker-compose.prod.yml exec redis redis-cli KEYS "quiz:*" | xargs docker compose -f docker-compose.prod.yml exec redis redis-cli DEL

# Clear all (use with caution)
docker compose -f docker-compose.prod.yml exec redis redis-cli FLUSHALL
```

### Update SSL Certificates

```bash
# Renew Let's Encrypt certificates
docker compose -f docker-compose.prod.yml exec certbot certbot renew

# Restart nginx
docker compose -f docker-compose.prod.yml restart nginx
```

---

## Monitoring Checklist

### Daily Checks
```bash
# Health check
curl -f https://yourdomain.com/health

# Check errors in Sentry
# Visit: https://sentry.io/organizations/your-org/projects/tgquiz/

# Check disk space
df -h

# Check recent errors
docker compose -f docker-compose.prod.yml logs --since 24h | grep ERROR | tail -20
```

### Weekly Checks
```bash
# Database size
docker compose -f docker-compose.prod.yml exec postgres \
  psql -U postgres -d tgquiznft_prod -c "SELECT pg_size_pretty(pg_database_size('tgquiznft_prod'));"

# Backup verification
ls -lh /backup/*.dump | tail -5

# TON wallet balance
docker compose -f docker-compose.prod.yml exec backend-api \
  python -c "from app.services.ton.wallet_service import WalletService; import asyncio; ws = WalletService(); print(asyncio.run(ws.get_balance()))"

# Review slow queries
docker compose -f docker-compose.prod.yml exec postgres \
  psql -U postgres -d tgquiznft_prod -c \
  "SELECT query, calls, total_time FROM pg_stat_statements ORDER BY total_time DESC LIMIT 5;"
```

---

## Emergency Contacts

- **DevOps Lead:** [Name] - [Email] - [Phone]
- **Backend Lead:** [Name] - [Email] - [Phone]
- **On-Call Engineer:** [Rotation Schedule]
- **Telegram Support Channel:** @your_support_channel

---

## Post-Incident Template

```markdown
## Incident Report: [Title]

**Date:** YYYY-MM-DD
**Duration:** XX minutes
**Severity:** PX
**Status:** Resolved / Investigating

### Timeline
- HH:MM - Incident detected
- HH:MM - Investigation started
- HH:MM - Root cause identified
- HH:MM - Fix applied
- HH:MM - Service restored

### Impact
- Users affected: XX
- Services impacted: [List]
- Data loss: None / [Description]

### Root Cause
[Detailed explanation]

### Resolution
[What was done to fix]

### Action Items
- [ ] [Prevention measure 1]
- [ ] [Prevention measure 2]
- [ ] Update runbook with new procedures

### Lessons Learned
[What we learned from this incident]
```

---

**Remember:** Stay calm, communicate clearly, and document everything!
