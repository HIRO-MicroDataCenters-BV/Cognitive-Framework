"""
KFP Run Details schema for the Cognitive Engine API.

This module defines the Pydantic models for KFP run details information,
including the base model and the model with additional fields.

Classes:
    RunDetailsBase: Base model for run details information.
    RunDetails: Model for run details information with additional fields.

Attributes:
    RunDetailsBase: Base model for run details information.
    RunDetails: Model for run details information with additional fields.
"""

from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field, validator


class RunDetailsBase(BaseModel):
    """
    Class that represents  run details
    """

    uuid: str
    display_name: Optional[str] = None
    name: str
    description: Optional[str] = None
    experiment_uuid: str
    pipeline_uuid: str
    createdAt_in_sec: datetime
    scheduledAt_in_sec: Optional[datetime] = None
    finishedAt_in_sec: Optional[datetime] = None
    state: Optional[str] = None

    @classmethod
    @validator("createdAt_in_sec", "finishedAt_in_sec", "scheduledAt_in_sec", pre=True)
    def parse_datetime(cls, value):
        """
        method to parse datetime to iso format
        :param value: value to formatted
        :return:
        """
        if isinstance(value, str):
            return datetime.fromisoformat(value)
        return value


class RunDetail(BaseModel):
    """
    Class that represents run details related to model
    """

    uuid: str
    name: str
    state: str
    description: Optional[str] = None
    createdAt_in_sec: datetime = Field(alias="created_at")
    scheduledAt_in_sec: Optional[datetime] = Field(None, alias="scheduled_at")
    finishedAt_in_sec: Optional[datetime] = Field(None, alias="finished_at")

    class Config:
        """
        orm_mode: True
        """

        orm_mode: Literal[True] = True
        from_attributes: Literal[True] = True
        allow_population_by_field_name = True


class RunDetails(RunDetailsBase):
    """
    Pass
    """

    class Config:
        """
        orm_mode: True
        """

        orm_mode: Literal[True] = True
        from_attributes: Literal[True] = True


class PipelineRunOutput(BaseModel):
    """
    Class that represents input details for a pipeline run.
    """

    run_name: Optional[str] = None
    run_id: Optional[str] = None
    status: Optional[str] = None
    duration: Optional[str] = None
    experiment_id: Optional[str] = None
    start_time: Optional[datetime] = None


class PipelineRunDetails(PipelineRunOutput):
    """
    Class that represents detailed pipeline run information.
    """

    id: int

    class Config:
        """
        Enable ORM mode for database integration.
        """

        orm_mode: Literal[True] = True
        from_attributes: Literal[True] = True
