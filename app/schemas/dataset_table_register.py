"""
Dataset table register schema for the Cognitive Engine API.

This module defines the Pydantic models for dataset table register information,
including the base model and the model with additional fields.

Classes:
    DatasetTableRegisterBase: Base model for dataset table register information.
    DatasetTableRegister: Model for dataset table register information with additional fields.

Attributes:
    DatasetTableRegisterBase: Base model for dataset table register information.
    DatasetTableRegister: Model for dataset table register information with additional fields.
"""

from datetime import datetime
from enum import IntEnum
from typing import Literal

from pydantic import BaseModel, Field, validator

from app.utils.cog_utils import S3Utils
from config import constants as const


class DatasetTypeEnum(IntEnum):
    """
    Enum class for dataset type
    """

    TRAIN = 0
    INFERENCE = 1
    BOTH = 2

    @classmethod
    def validate(cls, value: int):
        """Validate if the provided value is a valid enum."""
        try:
            return cls(value)
        except ValueError:
            raise ValueError(const.DATASET_TYPE_ERROR_MESSAGE)


class DatasetType(BaseModel):
    """
    DatasetType validator class
    """

    # Bug : FastAPI by default doesn't validate enum values.
    # Issue No : https://github.com/fastapi/fastapi/issues/2129
    # Fix : Read as IntEnum value , convert to DatasetTypeEnum and added custom validator
    dataset_type: DatasetTypeEnum = Field(
        ..., description="Must be 0 (train data), 1 (inference data), or 2 (both)."
    )

    @validator("dataset_type", pre=True)
    def check_dataset_type(cls, value):
        """
        validator to check of dataset_type in the given range
        """
        return DatasetTypeEnum.validate(int(value))


class DatasetTableRegisterBase(BaseModel):
    """
    Class that represents  dataset table register details
    """

    dataset_id: int
    # user_id: int To be replaced with user service
    db_url: str
    table_name: str
    fields_selected_list: str


class DatasetTable(DatasetType):
    """
    Class that represents dataset table register post details
    """

    name: str
    description: str
    db_url: str
    table_name: str
    selected_fields: str

    @validator("db_url")
    def validate_db_url(cls, value):
        """
        validator function to validate db_url
        """
        if not S3Utils.validate_db_url(value):
            raise ValueError(
                "Invalid db_url format. Ensure it matches the required pattern."
            )
        return value


class DatasetTableResponse(BaseModel):
    """
    Class that represents dataset table register response details
    """

    id: int
    dataset_id: int
    dataset_name: str
    description: str
    dataset_type: int
    db_url: str
    table_name: str
    fields_selected_list: str
    register_date: datetime


class DatasetTableRegister(DatasetTableRegisterBase):
    """
    Class that represents  dataset table register details
    """

    id: int
    register_date: datetime
    dataset_name: str
    description: str
    dataset_type: int

    class Config:
        """orm_mode: True"""

        orm_mode: Literal[True] = True
        from_attributes: Literal[True] = True
