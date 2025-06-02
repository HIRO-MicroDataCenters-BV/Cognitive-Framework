"""
Model File Upload schema for the Cognitive Engine API.

This module defines the Pydantic models for model file upload information,
including the base model and the model with additional fields.

Classes:
    ModelFileUploadBase: Base model for model file upload information.
    ModelFileUpload: Model for model file upload information with additional fields.

Attributes:
    ModelFileUploadBase: Base model for model file upload information.
    ModelFileUpload: Model for model file upload information with additional fields.
"""

from datetime import datetime
from enum import IntEnum
from typing import Optional, Literal

from pydantic import BaseModel, Field, validator

from config import constants as const


class ModelFileTypeEnum(IntEnum):
    """
    Enum for model file type
    """

    POLICY = "0"
    NON_POLICY = "1"


class FileTypeValidatorBase(BaseModel):
    """
    Base class with file_type field and validation to avoid repetition.
    """

    # Bug : FastAPI by default doesn't validate enum values.
    # Issue No : https://github.com/fastapi/fastapi/issues/2129
    # Fix : Read as IntEnum value , convert to ModelFileTypeEnum and added custom validator
    file_type: ModelFileTypeEnum = Field(
        ...,
        description="Must be 0 or 1. (0 - Model Policy File Upload, "
        "1 - Model File Upload)",
    )

    @classmethod
    @validator("file_type", pre=True)
    def check_file_type(cls, value):
        """
        Validator to check if file_type is in the given range
        """
        if not isinstance(value, ModelFileTypeEnum):
            raise ValueError(const.MODEL_TYPE_ERROR_MESSAGE)
        return value


class ModelFileUploadBase(FileTypeValidatorBase):
    """
    Class that represents  model file upload details
    """

    model_id: int
    register_date: datetime
    file_name: str
    file_path: str
    file_description: Optional[str] = None


class ModelFileUploadGet(BaseModel):
    """
    Class that represents model file upload retrieval details
    """

    model_id: int
    file_name: str


class ModelUploadUriPost(FileTypeValidatorBase):
    """
    Class that represents model upload post details
    """

    model_id: int
    description: str
    uri: str


class ModelFileUploadPost(FileTypeValidatorBase):
    """
    Class that represents model file upload post details
    """

    file_description: Optional[str] = None
    model_id: int


class ModelFileUploadPut(BaseModel):
    """
    Class that represents model file update put details
    """

    model_id: int
    id: int
    file_description: Optional[str] = None


class ModelFileUploadDetails(BaseModel):
    """
    Class that represents model file details
    """

    id: int = Field(alias="file_id")
    file_name: str

    # file_description: Optional[str] = None
    class Config:
        """
        orm_mode: True
        """

        orm_mode: Literal[True] = True
        from_attributes: Literal[True] = True
        allow_population_by_field_name = True


class ModelFileUpload(ModelFileUploadBase):
    """
    Class that represents  model file upload details
    """

    id: int

    class Config:
        """
        orm_mode: True
        """

        orm_mode: Literal[True] = True
        from_attributes: Literal[True] = True
