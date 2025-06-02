"""
    DB model class for BrokerDetails
"""

import ipaddress
from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Sequence,
    DateTime,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship, validates

from app.db.session import Base


class BrokerDetails(Base):
    """
    DB model class for Broker Details.

    The following attributes of message broker details are stored in this table:
        * id - Unique identifier for the Broker
        * broker_name - Name of the Broker
        * broker_ip - IP address of the Broker
        * broker_port - Port of the Broker
        * creation_date - creation date of Broker
    """

    __tablename__ = "broker_details"
    id = Column(Integer, Sequence("broker_details_id_seq"), primary_key=True)
    broker_name = Column(String, nullable=False)
    broker_ip = Column(String, nullable=False)
    broker_port = Column(Integer, nullable=False)
    creation_date = Column(DateTime, default=datetime.utcnow, nullable=False)

    @validates("broker_ip")
    def validate_broker_ip(self, key, broker_ip):
        """
        validates the broker ip
        Args:
            key:
            broker_ip:

        Returns:
             str: IP address of the Broker
        """
        try:
            return str(ipaddress.ip_address(broker_ip))  # Validates both IPv4 and IPv6
        except ValueError:
            raise ValueError(f"Invalid IP address format: {broker_ip}")

    broker_topic = relationship(
        "TopicDetails",
        back_populates="broker_topic_register",
        cascade="all, delete",
    )
    __table_args__ = (
        UniqueConstraint(
            "broker_name",
            name="unique_broker_per_dataset",
        ),
    )
