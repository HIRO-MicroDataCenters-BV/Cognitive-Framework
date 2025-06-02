"""
Validation Metric Info schema for the Cognitive Engine API.

This module defines the Pydantic models for validation metric information,
 including the base model and the model with additional fields.

Classes:
    ValidationMetricBase: Base model for validation metric information.
    ValidationMetric: Model for validation metric information with additional fields.

Attributes:
    ValidationMetricBase: Base model for validation metric information.
    ValidationMetric: Model for validation metric information with additional fields.
"""

from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel


class ValidationMetricInput(BaseModel):
    """
    Class that represents  validation metric input details
    """

    model_name: Optional[str] = None
    accuracy_score: Optional[float] = None
    example_count: Optional[int] = None
    f1_score: Optional[float] = None
    log_loss: Optional[float] = None
    precision_score: Optional[float] = None
    recall_score: Optional[float] = None
    roc_auc: Optional[int] = None
    score: Optional[float] = None
    cpu_consumption: Optional[float] = None
    memory_utilization: Optional[float] = None


class ValidationMetricBase(ValidationMetricInput):
    """
    Class that represents  validation metric details
    """

    model_id: Optional[int] = None
    dataset_id: Optional[int] = None
    registered_date_time: Optional[datetime] = None


class ValidationMetricDetails(BaseModel):
    """
    Class that represents validation metric details related to model
    """

    id: int
    dataset_id: int
    registered_date_time: datetime
    accuracy_score: float
    example_count: int
    f1_score: float
    log_loss: float
    precision_score: float
    recall_score: float
    roc_auc: int
    score: float
    cpu_consumption: float
    memory_utilization: float

    class Config:
        """
        orm_mode: True
        """

        orm_mode: Literal[True] = True
        from_attributes: Literal[True] = True


class ValidationMetric(ValidationMetricBase):
    """
    Class that represents  validation metric details
    """

    id: int

    class Config:
        """
        orm_mode: True
        """

        orm_mode: Literal[True] = True
        from_attributes: Literal[True] = True
        fields = {"model_name": {"exclude": True}}  # Exclude password when returning
