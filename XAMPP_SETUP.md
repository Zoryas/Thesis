# ReadWise XAMPP + MySQL Setup

## 1) Start XAMPP Services
- Start `Apache`
- Start `MySQL`

## 2) Create Python Environment
```powershell
python -m venv .venv
.\\.venv\\Scripts\\Activate.ps1
pip install -r requirements.txt
```

## 3) Configure DB (optional)
Default values are:
- host: `127.0.0.1`
- port: `3306`
- user: `root`
- password: empty
- database: `readwise_db`

Override with environment variables if needed:
- `READWISE_DB_HOST`
- `READWISE_DB_PORT`
- `READWISE_DB_USER`
- `READWISE_DB_PASSWORD`
- `READWISE_DB_NAME`

## 4) Run Flask API
```powershell
python app.py
```

The app auto-creates schema and seed data on startup.

## 5) Open Frontend from Apache
- `http://localhost/readwise/login.html`

Flask API base URL used by frontend:
- `http://localhost:5000`

## Seed Accounts
- Teacher: `ms.villanueva@pnhs.edu` / `teacher123`
- Teacher: `teacher@example.com` / `abcd`
- Student: `juan.delacruz@pnhs.edu` / `password123`
- Student: `maria.santos@pnhs.edu` / `password123`
- Student: `carlo.reyes@pnhs.edu` / `password123`
