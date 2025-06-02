"""
    DB model class for kfp experiments details
"""

from datetime import datetime
from sqlalchemy import Column, String, DateTime
from sqlalchemy.orm import relationship
from app.db.session import Base


class Experiment(Base):
    """
    Represents an experiment entity.

    Attributes:
        uuid (str): The unique identifier for the experiment.
        name (str): The name of the experiment.
        description (str): The description of the experiment.
        createdatinSec (int): The timestamp when the experiment was created.
    """

    __tablename__ = "experiments"

    uuid = Column(String(255), primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(String(255), nullable=False)
    createdatinSec = Column(DateTime, default=datetime.utcnow, nullable=False)
    run_details = relationship(
        "RunDetails", back_populates="experiments", cascade="all, delete-orphan"
    )
    pipelines = relationship(
        "Pipeline", back_populates="experiments", cascade="all, delete-orphan"
    )
