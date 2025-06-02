"""
Dataset information schema for the Cognitive Engine API.

This module defines the Pydantic models for dataset information,
including the base model and the model with additional fields.

Classes:
    DatasetInfoBase: Base model for dataset information.
    DatasetInfo: Model for dataset information with additional fields.

Attributes:
    DatasetInfoBase: Base model for dataset information.
    DatasetInfo: Model for dataset information with additional fields.
"""

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class DatasetInfoBase(BaseModel):
    """
    Class that represents  dataset details
    """

    user_id: int
    register_date_time: datetime
    last_modified_time: datetime
    last_modified_user_id: int


class DatasetInfoDetails(BaseModel):
    """
    Class that represents dataset details related to model
    """

    id: Optional[int]
    dataset_name: str
    description: Optional[str]
    train_and_inference_type: int = Field(alias="dataset_type")
    data_source_type: int

    class Config:
        """
        orm_mode: True
        """

        orm_mode: Literal[True] = True
        from_attributes: Literal[True] = True
        allow_population_by_field_name = True


class DatasetInfo(DatasetInfoBase):
    """
    Class that represents  dataset details
    """

    id: int

    class Config:
        """
        orm_mode: True
        """

        orm_mode: Literal[True] = True
        from_attributes: Literal[True] = True
