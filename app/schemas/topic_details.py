"""
Topic details schema .

This module defines the Pydantic models for topic information, including the base model.

Classes:
    TopicBase: Base model for Topic details.
    TopicResponse: Topic Response

"""
from datetime import datetime
from typing import Literal, Dict, Any, Optional
from enum import Enum
from pydantic import BaseModel, Field

from config import constants as const


class TopicBase(BaseModel):
    """
    Class that represents topic details.
    """

    name: str
    schema_definition: Dict[str, Any] = Field(..., alias="schema")


class TopicUpdate(BaseModel):
    """
    Class that represents topic update details.
    """

    topic_name: Optional[str] = Field(alias="name")
    topic_schema: Optional[Dict[str, Any]] = Field(alias="schema")


# Define an Enum for offset_reset validation
class OffsetReset(str, Enum):
    """
    Class that OffsetReset messages to fetch.
    """

    earliest = const.EARLIEST  # pylint: disable=invalid-name
    latest = const.LATEST  # pylint: disable=invalid-name


class TopicResponse(BaseModel):
    """
    Class that represents Broker response details.
    """

    id: int
    topic_name: str
    topic_schema: Dict[str, Any]
    broker_id: int
    creation_date: datetime

    class Config:
        """
        orm_mode: True
        """

        orm_mode: Literal[True] = True
        from_attributes: Literal[True] = True
        arbitrary_types_allowed = True
