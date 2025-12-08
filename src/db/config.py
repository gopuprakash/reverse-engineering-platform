import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from src.config import settings

load_dotenv()

db_password = os.getenv("DB_PASSWORD") or os.getenv("RE_KB_DB_PASSWORD") or ""
print(f"DEBUG: Password found: '{db_password}'")

# Construct URL from your pydantic settings
DATABASE_URL = f"postgresql://{settings.kb_db_user}:{db_password}@{settings.kb_db_host}:{settings.kb_db_port}/{settings.kb_db_name}"

# 3. Create the Engine
engine = create_engine(DATABASE_URL, pool_size=20, max_overflow=0)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base() 

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()