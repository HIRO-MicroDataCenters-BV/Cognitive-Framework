"""
    DB model class for DatasetTopicDetails
"""

from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    DateTime,
    ForeignKey,
)
from sqlalchemy.orm import relationship

from app.db.session import Base


class DatasetTopicDetails(Base):
    """
    Class that represents dataset_topic_details information
    The following attributes of a dataset_topic_details are stored in this table:
    * id - id of the dataset
    * dataset_id - dataset id
    * topic_id - topic id
    * creation_date - date of registering the dataset
    """

    __tablename__ = "dataset_topic_details"
    id = Column(Integer, primary_key=True, index=True)
    topic_id = Column(Integer, ForeignKey("topic_details.id"))
    dataset_id = Column(Integer, ForeignKey("dataset_info.id"))
    creation_date = Column(DateTime, default=datetime.utcnow, nullable=False)

    topic_info = relationship("TopicDetails", back_populates="dataset_topic_info")

    dataset_topic = relationship("DatasetInfo", back_populates="dataset_topic_mapping")
