"""
BrokerTopic details schema .

This module defines the Pydantic models for dataset registration
 of broker and topic information,including the base model.

Classes:
    DatasetBrokerTopicBase: Base model for dataset registration of broker and topic details.
    DatasetBrokerTopicResponse Model: Response model for dataset registration of broker and topic details

"""

from typing import Literal, List, Any

from pydantic import BaseModel, Field, IPvAnyAddress

from app.schemas.broker_details import BrokerResponse
from app.schemas.dataset_info import DatasetInfoDetails
from app.schemas.dataset_table_register import DatasetType
from app.schemas.topic_details import TopicResponse


class DatasetBrokerTopicBase(DatasetType):
    """
    Class that represents dataset broker topic registration details.
    """

    name: str
    description: str
    broker_id: int = Field(..., gt=0, description="Broker ID")
    topic_id: int = Field(..., gt=0, description="Broker ID")


class DatasetTopicData(BaseModel):
    """
    Class that represents Topic Data response details.
    """

    dataset_id: int
    records: List[Any]
    record_count: int
    topic_name: str


class BrokerTopicDetails(BaseModel):
    """
    Class that represents Broker Topic details.
    """

    topic_name: str
    broker_ip: IPvAnyAddress
    broker_port: int


class DatasetBrokerTopicResponse(BaseModel):
    """
    Class that represents Dataset Broker and topic response details.
    """

    dataset: DatasetInfoDetails
    broker_details: BrokerResponse
    topic_details: TopicResponse

    class Config:
        """
        orm_mode: True
        """

        orm_mode: Literal[True] = True
        from_attributes: Literal[True] = True
