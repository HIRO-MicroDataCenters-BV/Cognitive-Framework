"""
KFP Tasks Info schema for the Cognitive Engine API.

This module defines the Pydantic models for KFP task information,
including the base model and the model with additional fields.

Classes:
    TaskBase: Base model for task information.
    Task: Model for task information with additional fields.

Attributes:
    TaskBase: Base model for task information.
    Task: Model for task information with additional fields.
"""

from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel


class TaskBase(BaseModel):
    """
    Class that represents  task details
    """

    uuid: str
    runuuid: str
    createdtimestamp: datetime
    startedtimestamp: datetime
    finishedtimestamp: datetime
    state: Optional[str] = None
    name: Optional[str] = None
    parenttaskuuid: Optional[str] = None


class Task(TaskBase):
    """
    PASS
    """

    class Config:
        """
        orm_mode: True
        """

        orm_mode: Literal[True] = True
        from_attributes: Literal[True] = True
