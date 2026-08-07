import os
import sys

from app import run_migrations


def main():
    applied = run_migrations()
    print("Applied migrations:", applied or "none")
    return 0


if __name__ == "__main__":
    sys.exit(main())
