# Forewise — Operations Runbook

## Architecture

```
Client -> Nginx (SSL, :443) -> Gunicorn (17 workers, :8000) -> FastAPI -> PostgreSQL 16
                             -> Static files (dist/)
```

- Server: DigitalOcean (single node)
- Backend: systemd service `forewise.service`
- Frontend: Static build in `/root/forewise/app_frontend/dist/`
- Database: PostgreSQL 16 with PostGIS
- Redis: Disabled (REDIS_ENABLED=false)

## Deploy

Automated via GitHub Actions on push to `main`:
1. Pull code
2. Run backend tests
3. Pre-deploy DB backup
4. Build frontend
5. Restart backend
6. Health check
7. Reload nginx

Manual deploy:
```bash
cd /root/forewise
git pull origin main
cd app_backend && .venv/bin/python3 -m pytest tests/test_health_and_auth.py tests/test_status_transitions.py -v
cd ../app_frontend && npm run build
systemctl restart forewise.service
sleep 8 && curl -s http://localhost:8000/api/v1/health
systemctl reload nginx
```

## Rollback

```bash
cd /root/forewise
git log --oneline -5                    # find target commit
git checkout <commit-hash>              # checkout safe commit
cd app_frontend && npm run build        # rebuild frontend
systemctl restart forewise.service      # restart backend
```

## Backup

- Automated: daily at 02:00 UTC via cron
- Script: `/root/backups/db/backup.sh`
- Location: `/root/backups/db/forewise_YYYY-MM-DD.sql.gz`
- Retention: 30 days
- DB name: `forewise_prod`
- Log: `/root/backups/db/backup.log`

Manual backup:
```bash
bash /root/backups/db/backup.sh
```

## Restore

```bash
# Stop service
systemctl stop forewise.service

# Restore from backup
gunzip -c /root/backups/db/forewise_2026-03-25.sql.gz | sudo -u postgres psql forewise_prod

# Restart
systemctl start forewise.service
```

## Health Verification

```bash
# Service status
systemctl status forewise.service

# API health
curl -s http://localhost:8000/api/v1/health

# Nginx status
systemctl status nginx

# PostgreSQL status
systemctl status postgresql@16-main

# Log tail
tail -50 /root/forewise/app_backend/logs/production.log

# DB connection
sudo -u postgres psql forewise_prod -c "SELECT COUNT(*) FROM users WHERE is_active=true;"
```

## Key Config Files

| File | Purpose |
|------|---------|
| `/root/forewise/app_backend/.env` | Environment variables |
| `/root/forewise/app_backend/gunicorn.conf.py` | Gunicorn config |
| `/etc/systemd/system/forewise.service` | Systemd service |
| `/etc/nginx/sites-enabled/forewise` | Nginx config |
| `/root/backups/db/backup.sh` | DB backup script |

## Known Limitations

1. **WebSocket**: In-memory per worker. Notifications are best-effort via WS; DB is source of truth.
2. **Rate Limiting**: In-memory per worker. Effective limit = N * configured limit.
3. **Redis**: Disabled. When enabled, will improve WS reliability and rate limiting.
4. **Single Server**: No HA/failover. Single point of failure.
