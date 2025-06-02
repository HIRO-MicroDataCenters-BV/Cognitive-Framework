"""
Validation Artifact Info schema for the Cognitive Engine API.

This module defines the Pydantic models for validation artifact information,
including the base model and the model with additional fields.

Classes:
    ValidationArtifactBase: Base model for validation artifact information.
    ValidationArtifact: Model for validation artifact information with additional fields.

Attributes:
    ValidationArtifactBase: Base model for validation artifact information.
    ValidationArtifact: Model for validation artifact information with additional fields.
"""

from typing import Dict, Literal, Optional

from pydantic import BaseModel


class Artifact(BaseModel):
    """
    Class that represents  artifact details
    """

    uri: str


class ValidationArtifactInput(BaseModel):
    """
    Class that represents  validation artifact input details
    """

    model_name: Optional[str] = None
    validation_artifacts: Optional[Dict[str, str]] = None


class ValidationArtifactBase(ValidationArtifactInput):
    """
    Class that represents  validation artifact details
    """

    model_id: Optional[int] = None
    dataset_id: Optional[int] = None


class ValidationArtifactDetails(BaseModel):
    """
    Class that represents validation artifact details related to model
    """

    id: int
    dataset_id: int
    validation_artifacts: Optional[Dict[str, str]]

    class Config:
        """
        orm_mode: True
        """

        orm_mode: Literal[True] = True
        from_attributes: Literal[True] = True
        allow_population_by_field_name = True


class ValidationArtifact(ValidationArtifactBase):
    """
    Class that represents  validation artifact details
    """

    id: int

    class Config:
        """
        orm_mode: True
        """

        orm_mode: Literal[True] = True
        from_attributes: Literal[True] = True
        fields = {"model_name": {"exclude": True}}  # Exclude password when returning
