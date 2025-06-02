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
from typing import Optional

from pydantic import BaseModel

from app.schemas.dataset_table_register import DatasetType


class DatasetUploadBase(DatasetType):
    """
    Class that represents  dataset upload details
    """

    dataset_name: str
    description: Optional[str] = None


class DatasetUpdateBase(BaseModel):
    """
    Class that represents  dataset update details
    """

    id: int
    name: str
    description: Optional[str] = None
    dataset_type: int


class DatasetUpload(BaseModel):
    """
    Class that represents dataset upload details
    """

    id: int
    dataset_id: int
    # last_modified_user_id: int To be replaced by user service module
    register_date: datetime
    file_name: str
    file_path: str

    class Config:
        """
        orm_mode: True
        """

        orm_mode = True
        from_attributes = True


class DatasetUploadResponse(BaseModel):
    """
    Class that represents dataset upload complete details
    """

    id: int
    dataset_id: int
    file_path: str
    file_name: Optional[str]
    register_date: datetime
    description: Optional[str]
    dataset_name: str
    dataset_type: int
