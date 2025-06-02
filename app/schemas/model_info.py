"""
Model Info schema for the Cognitive Engine API.

This module defines the Pydantic models for model information, including the base model
and the model with additional fields.

Classes:
    ModelInfoBase: Base model for model information.
    ModelInfo: Model for model information with additional fields.

Attributes:
    ModelInfoBase: Base model for model information.
    ModelInfo: Model for model information with additional fields.
"""

from datetime import datetime
from typing import Optional, Literal

from pydantic import BaseModel, StrictStr, StrictInt

from app.schemas.model_upload import FileTypeValidatorBase


class ModelInfoBase(BaseModel):
    """
    Class that represents model details
    """

    name: str
    version: int
    type: str
    description: Optional[str] = None


class ModelInfoUpdate(BaseModel):
    """
    Class that represents model update details
    """

    name: Optional[StrictStr] = None
    version: Optional[StrictInt] = None
    type: Optional[StrictStr] = None
    description: Optional[StrictStr] = None


class ModelDeploy(BaseModel):
    """
    Class that represents  model deploy details
    """

    name: str
    version: str
    isvc_name: str


class ModelUri(FileTypeValidatorBase):
    """
    Class that represents  model save details
    """

    name: str
    description: str


class ModelInfo(ModelInfoBase):
    """
    Class that represents  model details
    """

    id: int
    last_modified_time: datetime
    register_date: datetime

    class Config:
        """
        orm_mode: True
        """

        orm_mode: Literal[True] = True
        from_attributes: Literal[True] = True
