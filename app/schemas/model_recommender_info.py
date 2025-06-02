"""
Best Model Recommender Info schema for the Cognitive Engine API.

This module defines the Pydantic models for Best Model Recommender information,
including the base model.
"""

from typing import Optional, Literal
from pydantic import BaseModel


class ModelRecommendationOutput(BaseModel):
    """
    Class that represents the output details of the model recommendation.

    Fields:
        id (Optional[int]): The ID of the recommended model.
        model_name (Optional[str]): The name of the recommended model.
        avg_f1_score (Optional[float]): The average F1 score of the model.
        avg_accuracy (Optional[float]): The average accuracy of the model.
        combined_score (Optional[float]): A combined score of the relevant metrics.
    """

    id: Optional[int] = None
    model_name: Optional[str] = None
    avg_f1_score: Optional[float] = None
    avg_accuracy: Optional[float] = None
    combined_score: Optional[float] = None

    class Config:
        """
        ORM configuration to enable reading from ORM objects and attributes.
        """

        orm_mode: Literal[True] = True
        from_attributes: Literal[True] = True
