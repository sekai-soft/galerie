from pathlib import Path
from sqlalchemy import text
from .db import db


def run_migrations():
    """Run all database migrations. All migrations should be idempotent."""
    migrations_dir = Path(__file__).parent / 'db_migrations'

    if not migrations_dir.exists():
        print("No db_migrations directory found.")
        return

    sql_files = sorted(migrations_dir.glob('*.sql'))

    if not sql_files:
        print("No migration files found.")
        return

    print(f"Running {len(sql_files)} migration(s):")

    for filepath in sql_files:
        with open(filepath, 'r') as f:
            sql = f.read()

        db.session.execute(text(sql))
        db.session.commit()

        print(f"✓ {filepath.name}")

    print(f"\nSuccessfully ran {len(sql_files)} migration(s).")
