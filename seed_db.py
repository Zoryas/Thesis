import os

os.environ.setdefault("READWISE_SKIP_AUTO_INIT", "1")

from app import init_database


if __name__ == "__main__":
    print("Running database initialization and seeding...")
    ok = init_database()
    if ok:
        print("Database initialization completed successfully.")
    else:
        print("Database initialization failed.")
        raise SystemExit(1)
