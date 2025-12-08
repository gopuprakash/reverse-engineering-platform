from sqlalchemy import text
from src.db.config import engine, DATABASE_URL

print(f"Resetting DB at: {DATABASE_URL}")
with engine.connect() as conn:
    conn.execution_options(isolation_level="AUTOCOMMIT")
    # Drops all tables with CASCADE to handle the foreign keys
    conn.execute(text("DROP SCHEMA public CASCADE; CREATE SCHEMA public;"))
    print("Database wiped successfully.")