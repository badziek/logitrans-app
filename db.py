# db.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

# Użyj PostgreSQL na serwerze, SQLite lokalnie
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///logitransport.db")

# Konfiguracja silnika bazy danych
if DATABASE_URL.startswith("sqlite"):
    # SQLite - wyłącz check_same_thread dla Flask
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        future=True,
    )
else:
    # PostgreSQL - standardowa konfiguracja
    engine = create_engine(DATABASE_URL, future=True)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
