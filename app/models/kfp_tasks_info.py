"""
    DB model class for kfp task details
"""

from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.db.session import Base


class Task(Base):
    """
    Represents a task entity.

    Attributes:
        uuid (str): The unique identifier for the task.
        runuuid (str): The unique identifier for the run associated with the task.
        createdtimestamp : The timestamp when the task was created.
        startedtimestamp : The timestamp when the task was started.
        finishedtimestamp : The timestamp when the task was finished.
        name (str): The name of the task.
        parenttaskuuid (str): The UUID of the parent task if this task is a child task.
        state (str): The state of the task.
    """

    __tablename__ = "tasks"
    uuid = Column(String(255), primary_key=True)
    runuuid = Column(String(255), ForeignKey("run_details.uuid"), nullable=False)
    createdtimestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    startedtimestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    finishedtimestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    state = Column(String(255))
    name = Column(String(255))
    parenttaskuuid = Column(String(255))
    run_details = relationship("RunDetails", back_populates="tasks")
