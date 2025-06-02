"""
KFP Experiments schema for the Cognitive Engine API.

This module defines the Pydantic models for KFP experiment information,
including the base model and the model with additional fields.

Classes:
    ExperimentBase: Base model for experiment information.
    Experiment: Model for experiment information with additional fields.

Attributes:
    ExperimentBase: Base model for experiment information.
    Experiment: Model for experiment information with additional fields.
"""

from datetime import datetime

from typing import List, Optional, Literal
from pydantic import BaseModel, Field

from app.schemas.kfp_run_details import RunDetail
from app.schemas.kfp_pipeline import Pipeline


class ExperimentBase(BaseModel):
    """
    Class that represents  experiment details
    """

    name: str
    description: str
    uuid: str
    createdatinSec: datetime


class ExperimentDetails(BaseModel):
    """
    Class that represents experiment details related to model
    """

    uuid: str
    name: str
    createdatinSec: datetime = Field(alias="created_at")

    class Config:
        """
        orm_mode: True
        """

        orm_mode: Literal[True] = True
        from_attributes: Literal[True] = True
        allow_population_by_field_name = True


class Experiment(ExperimentBase):
    """
    Class that represents  experiment details
    """

    run_details: Optional[List[RunDetail]] = []
    pipelines: Optional[List[Pipeline]] = []

    class Config:
        """
        orm_mode: True
        """

        orm_mode: Literal[True] = True
        from_attributes: Literal[True] = True
