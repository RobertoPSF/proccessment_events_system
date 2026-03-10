import time
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = "postgresql://postgres:postgres@db:5432/events_db"

MAX_RETRIES = 10
RETRY_DELAY = 3

for i in range(MAX_RETRIES):
    try:
        engine = create_engine(DATABASE_URL)
        conn = engine.connect()
        conn.close()
        print("Database connected!")
        break
    except Exception:
        print("Database not ready, retrying...")
        time.sleep(RETRY_DELAY)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()