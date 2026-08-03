import sys
from pathlib import Path

# Ensure parent folder (project root) is on sys.path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from db_migrate_backfill import verify_questions_and_choices  # noqa: E402

passage_id = sys.argv[1] if len(sys.argv) > 1 else "p48"
print(verify_questions_and_choices(passage_id))
