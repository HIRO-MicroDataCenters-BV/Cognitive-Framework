"""
Broker details schema .

This module defines the Pydantic models for broker information, including the base model.

Classes:
    BrokerBase: Base model for Broker details.
    BrokerResponse: Broker Response

"""
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, IPvAnyAddress, Field


class BrokerBase(BaseModel):
    """
    Class that represents broker details.
    """

    name: str
    ip: IPvAnyAddress
    port: int = Field(gt=0, description="Broker port")


class BrokerUpdate(BaseModel):
    """
    Class that represents broker update details.
    """

    broker_name: Optional[str] = Field(alias="name", description="Broker name")
    broker_ip: Optional[IPvAnyAddress] = Field(alias="ip", description="Broker ip")
    broker_port: Optional[int] = Field(gt=0, description="Broker port", alias="port")


class BrokerResponse(BaseModel):
    """
    Class that represents Broker response details.
    """

    id: int
    broker_name: str
    broker_ip: IPvAnyAddress
    broker_port: int
    creation_date: datetime

    class Config:
        """
        orm_mode: True
        """

        orm_mode: Literal[True] = True
        from_attributes: Literal[True] = True
