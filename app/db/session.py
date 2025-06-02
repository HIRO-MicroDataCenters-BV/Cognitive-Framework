"""
Database session management for the Cognitive Engine API.

This module sets up the database engine, session, and base class for the ORM models.
It also provides a function to get a database session.

Attributes:
    DATABASE_URL (str): The database URL for the SQLite database.
    engine (Engine): The SQLAlchemy engine connected to the SQLite database.
    SessionLocal (sessionmaker): A configured sessionmaker for creating database sessions.
    Base (declarative_base): The base class for all ORM models.

Functions:
    get_db: Provides a database session for use in dependency injection.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import constants as const


is_testing = os.getenv("TESTING", "False") == "True"

db_user = os.getenv(const.DB_USER)
db_password = os.getenv(const.DB_PASSWORD)
db_host = os.getenv(const.DB_HOST)
db_port = os.getenv(const.DB_PORT)
db_name = os.getenv(const.DB_NAME)

if is_testing:
    DATABASE_URL = "sqlite:///./test.db"
else:
    DATABASE_URL = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """
    Get DB session
    :return:
    """
    db_app = SessionLocal()
    try:
        yield db_app
    finally:
        db_app.close()
