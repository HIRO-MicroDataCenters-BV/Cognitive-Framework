"""
    DB model class for TopicDetails
"""

from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Sequence,
    DateTime,
    ForeignKey,
    JSON,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.db.session import Base


class TopicDetails(Base):
    """
    The following attributes of a topic_details are stored in this table:
           * id - topic id
           * topic_name - topic name
           * topic_schema - data in topic
           * broker_id - Broker id
           * creation_date - creation date of topic
    """

    __tablename__ = "topic_details"
    id = Column(Integer, Sequence("topic_details_id_seq"), primary_key=True)
    topic_name = Column(String)
    topic_schema = Column(JSON)
    broker_id = Column(Integer, ForeignKey("broker_details.id"))
    creation_date = Column(DateTime, default=datetime.utcnow, nullable=False)

    broker_topic_register = relationship("BrokerDetails", back_populates="broker_topic")
    dataset_topic_info = relationship(
        "DatasetTopicDetails",
        back_populates="topic_info",
        cascade="all, delete",
    )
    __table_args__ = (
        UniqueConstraint("topic_name", "broker_id", name="unique_topic_per_broker"),
    )
