# Deployment Readiness Guide

This guide summarizes the current deployment readiness state of the ReadWise app, and provides a step-by-step path to complete deployment preparation.

## 1. Current state

The app has a working deployment scaffold:

- `render.yaml` is present and configured to start the app with `gunicorn app:app`.
- `requirements.txt` includes `gunicorn`.
- `app.py` enforces production-only requirements for `READWISE_SECRET_KEY` and `READWISE_ALLOWED_ORIGINS`.
- `scripts/final_publish_check.py` exists to validate deployment manifest and environment variables.

However, the app is not yet fully ready for production deployment because required production environment variables are not configured and several deployment hardening and testing tasks remain open.

## 2. Required deployment environment variables

The production environment must define all of these variables:

- `READWISE_ENV=production`
  - Set this in your deployment platform to tell the app it is running in production mode.
- `READWISE_SECRET_KEY`
  - Generate a strong random secret and store it in your deployment provider's secret store.
  - Example generators: `openssl rand -base64 32` or Python `python -c "import secrets; print(secrets.token_urlsafe(32))"`.
- `READWISE_DB_HOST`
  - The hostname or IP address of your MySQL database server.
  - If you use a managed DB service, get this from the database provider.
- `READWISE_DB_PORT`
  - The port your MySQL instance listens on, usually `3306`.
- `READWISE_DB_USER`
  - The database username that the app will use to connect.
- `READWISE_DB_PASSWORD`
  - The password for the above database user.
- `READWISE_DB_NAME`
  - The name of the database schema used by ReadWise.
  - In production this is typically something like `readwise_db` or your chosen database name.
- `READWISE_ALLOWED_ORIGINS`
  - A comma-separated list of allowed front-end origins for CORS.
  - Use the production site URL(s), for example `https://readwise.example.com`.

### How to obtain these values

- `READWISE_SECRET_KEY`
  - Generate a strong random secret locally before deployment.
  - Example commands:
    - `openssl rand -base64 32`
    - `python -c "import secrets; print(secrets.token_urlsafe(32))"`
  - Save it into your deployment provider's secret store or environment settings.
- `READWISE_DB_HOST`, `READWISE_DB_PORT`, `READWISE_DB_USER`, `READWISE_DB_PASSWORD`, `READWISE_DB_NAME`
  - Obtain from the MySQL server or managed database service you will use.
  - Common places to get these values:
    - Your cloud provider's managed database dashboard (AWS RDS, Google Cloud SQL, Azure Database for MySQL)
    - Your deployment host's database add-on panel (Render, Railway, Heroku)
    - Your own MySQL server or VM if you self-host the database
  - Typical example values:
    - `READWISE_DB_HOST=readwise-db.example.com`
    - `READWISE_DB_PORT=3306`
    - `READWISE_DB_USER=readwise_user`
    - `READWISE_DB_PASSWORD=<your-db-password>`
    - `READWISE_DB_NAME=readwise_db`
- `READWISE_ALLOWED_ORIGINS`
  - Use the origin(s) of your deployed front-end app.
  - Example: `https://readwise.example.com`

These are required both by `app.py` and by the repository's readiness check script.

## 3. Validate deployment manifest and env vars

Run this command after the environment variables are configured:

```bash
python scripts/final_publish_check.py
```

If the environment is not configured yet, the script will report missing env vars.

## 3.1 Create a local `.env` file

A local `.env` file does not exist yet, but you can create one from the provided template:

```bash
copy .env.example .env
```

Then open `.env` and replace the placeholders with your production values.

For example:

```text
READWISE_ENV=production
READWISE_SECRET_KEY=<strong-random-secret>
READWISE_DB_HOST=<your-db-host>
READWISE_DB_PORT=3306
READWISE_DB_USER=<your-db-user>
READWISE_DB_PASSWORD=<your-db-password>
READWISE_DB_NAME=readwise_db
READWISE_ALLOWED_ORIGINS=https://your-production-domain.example.com
```

If you are using a deployment platform, set these values in the platform's environment settings rather than committing `.env` to source control.

## 4. Verify the runtime startup

From the repo root, start the app with the production entrypoint:

```bash
gunicorn app:app
```

If you are using Render or another host, confirm that the platform uses the same command.

## 5. Test the core student flow

At minimum, verify these critical student paths manually or with tests:

- Student login
- Student dashboard loads assigned passages
- Reading page loads and tracks reading time
- Student can lock passage and proceed to questions
- Student can submit answers
- Student results page loads backend result data

## 6. Run existing automated checks

Run the focused unit test file that already exists:

```bash
python -m unittest discover -s test -p "test_phase4_final_delivery.py"
```

If you want broader coverage, run the full test suite:

```bash
python -m unittest discover -s test
```

## 7. Review the deployment gap checklist

There are several open checklist items in `DEPLOYMENT_GAP_CHECKLIST.md`, including:

- Teacher page workflows
- Assignment and passage API validation
- Student reading progress and attempt endpoints
- Teacher reports endpoints
- Duplicate/ malformed payload handling
- Unauthorized request handling
- State transition integrity for `is_locked`, `is_submitted`, `completed_at`

Use that checklist as a more detailed task tracker.

## 8. Production hardening items

The app should also be hardened before production, including:

- Use a strong, random `READWISE_SECRET_KEY` in production
- Restrict `READWISE_ALLOWED_ORIGINS` to exact production origin(s)
- Ensure HTTPS-only cookies when `READWISE_ENV=production`
- Add login rate limiting / brute-force protection
- Add audit logs for key student and teacher actions
- Add structured logging and monitoring
- Add DB backup and restore procedures
- Add retry/backoff for transient failures
- Define an incident rollback plan
- Review DB indexes for high-traffic queries
- Load test critical endpoints
- Finalize `.env` and secret management
- Add a smoke-test script and healthcheck endpoint
- Define release checklist and sign-off process

## 9. Deployment checklist

1. Configure production environment variables.
2. Confirm `render.yaml` start command and env var keys are correct.
3. Run `python scripts/final_publish_check.py`.
4. Run application startup with `gunicorn app:app`.
5. Run unit tests and any smoke tests.
6. Manually validate student and teacher flows.
7. Confirm CORS/secret/HTTPS settings in production.
8. Deploy to staging first, then perform sanity tests.
9. Prepare rollback / restore instructions.

## 10. Useful reference documents

- `DEPLOYMENT_GAP_CHECKLIST.md`
- `PRODUCTION_PLAN_FINAL.md`
- `SYSTEM_FINALIZATION_PLAN.md`
- `TALASAAI_FINALIZATION_PRODUCTION_PLAN.md`
- `render.yaml`
- `scripts/final_publish_check.py`

## 11. Recommended next action

If you want to move forward now, the next practical step is:

1. Set the required production env vars.
2. Run `python scripts/final_publish_check.py`.
3. Fix any remaining manifest or environment issues reported by that script.

Once that passes, continue with the remaining API and UI validation items in `DEPLOYMENT_GAP_CHECKLIST.md`.
