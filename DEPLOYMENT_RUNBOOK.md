# ReadWise Deployment Runbook

## 1. Prerequisites
- Python 3.11+
- MySQL server reachable from the deployment host
- Environment variables configured before startup

## 2. Required environment variables
- READWISE_ENV=production
- READWISE_SECRET_KEY=<strong random value>
- READWISE_DB_HOST
- READWISE_DB_PORT
- READWISE_DB_USER
- READWISE_DB_PASSWORD
- READWISE_DB_NAME
- READWISE_ALLOWED_ORIGINS=<comma-separated allowed origins>
- READWISE_LOG_LEVEL=INFO

## 3. Startup
Run the app with Gunicorn:

```bash
gunicorn app:app --bind 0.0.0.0:8000
```

## 4. Database migration flow
The app checks for migration files under the migrations directory and applies them during startup.

To apply manually:

```bash
python -m app
```

## 5. Post-deploy verification
Run the smoke test:

```bash
python scripts/phase3_smoke_test.py
```

Expected result: the health and API health endpoints return HTTP 200.

## 6. Backup and restore
- Backup MySQL data with:

```bash
mysqldump -u <user> -p <database> > backup.sql
```

- Restore with:

```bash
mysql -u <user> -p <database> < backup.sql
```

## 7. Rollback guidance
- Revert to the previous release artifact
- Re-run the previous database state from backup if needed
- Re-run the smoke test after rollback
