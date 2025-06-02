"""
    DB model class for TopicDetails
"""

from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
)
from sqlalchemy.types import CHAR

from app.db.session import Base


class Users(Base):
    """
    The Users table stores information about users in the system.

    Attributes:
        id (int): The unique identifier for each user.
        email (str): The email address of the user.
        full_name (str): The full name of the user.
        user_name (str): The username for the user.
        org_id (int): The ID of the organization the user is associated with.
        country (str): The country of the user.
        phone (str): The phone number of the user.
        job_title (str): The job title of the user.
        user_level (int): The user level (junior, intermediate, senior, expert).
        password_updated_at (datetime): The timestamp when the user's password was last updated.
        created_at (datetime): The timestamp when the user was created.
        updated_at (datetime): The timestamp when the user was last updated.
    """

    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(100), nullable=False)
    full_name = Column(String(100), nullable=False)
    user_name = Column(String(100), nullable=False)
    org_id = Column(Integer, nullable=False)
    country = Column(CHAR(2), nullable=False)
    phone = Column(String(100), nullable=False)
    job_title = Column(String(100), nullable=False)
    user_level = Column(Integer, nullable=False)
    password_updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
