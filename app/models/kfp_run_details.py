"""
    DB model class for run details
"""

from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.db.session import Base


class RunDetails(Base):
    """
    Represents a run_details entity.

    Attributes:
        uuid (str): The unique identifier for the run_details.
        display_name (str): display name for the run details
        name (str): name for the run details
        description (str): description for the run details
        experiment_uuid (str) : experiment associated with the run
        pipeline_uuid (str): pipeline associated with the run
        createdAt_in_sec (int): The timestamp when the run is created.
        scheduledAt_in_sec (int): The scheduled timestamp of the run
        finishedAt_in_sec (int): The finished timestamp of the run
        state (str): status of the run
    """

    __tablename__ = "run_details"

    uuid = Column(String(255), primary_key=True)
    display_name = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(String(255))
    experiment_uuid = Column(
        String(255), ForeignKey("experiments.uuid"), nullable=False
    )
    pipeline_uuid = Column(String(255), nullable=False)
    createdAt_in_sec = Column(DateTime, default=datetime.utcnow, nullable=False)
    scheduledAt_in_sec = Column(DateTime, default=datetime.utcnow)
    finishedAt_in_sec = Column(DateTime, default=datetime.utcnow)
    state = Column(String(255))
    experiments = relationship("Experiment", back_populates="run_details")
    tasks = relationship(
        "Task", back_populates="run_details", cascade="all, delete-orphan"
    )
