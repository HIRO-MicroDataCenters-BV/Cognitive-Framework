"""
Standard Response schema for the Cognitive Engine API.

This module defines the Pydantic model for a standard response, which includes a status code,
a message, and data of a generic type.

Classes:
    StandardResponse: Model for a standard response.

Attributes:
    StandardResponse: Model for a standard response.
"""

from typing import TypeVar, Generic, Optional, Dict
from pydantic import BaseModel
from pydantic.generics import GenericModel

T = TypeVar("T")


class Pagination(BaseModel):
    """
    class for pagination to be added in response
    """

    page: int
    limit: int
    total_items: int


class StandardResponse(GenericModel, Generic[T]):
    """
    Class that represents a standard API response.
    """

    status_code: int
    message: str
    data: T
    pagination: Optional[Dict[str, int]] = None

    class Config:
        """
        Pydantic configuration for the StandardResponse model.
        """

        # This setting ensures that fields with value None are excluded from the output
        exclude_none = True

    def dict(self, *args, **kwargs):
        """
        Override the default `dict` method to exclude the `pagination` field if it is None.
        """
        exclude_fields = kwargs.pop("exclude", set()) or set()
        if self.pagination is None:
            exclude_fields.add("pagination")
        return super().dict(*args, **kwargs, exclude=exclude_fields)
