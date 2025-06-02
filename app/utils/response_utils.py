"""
Utility function for creating a standard response.

This module provides a function to create a standardized response dictionary.

Functions:
    standard_response: Creates a standardized response dictionary with a status code, message, and data.
"""

from typing import Any, Dict, Optional
from pydantic import BaseModel
from fastapi import Request


def standard_response(
    status_code: int, message: str, data: Any, request: Optional[Request] = None
) -> Dict[str, Any]:
    """
    Create a standard response dictionary.

    Args:
        :param status_code: The HTTP status code.
        :param message: The response message.
        :param data: The response data.
        :param request:

    Returns:
        Dict[str, Any]: The standard response dictionary.

    """
    # Initialize the response with the required fields
    response = {"status_code": status_code, "message": message}

    # Check for pagination and apply it
    pagination_details = None
    if (
        isinstance(data, list)
        and request
        and request.method == "GET"
        and hasattr(request.state, "pagination")
    ):
        pagination_details = request.state.pagination

        # Get the total count of items before slicing
        total_items = len(data)

        # Slice the data for pagination
        start_index = pagination_details["start_index"]
        end_index = pagination_details["end_index"]
        data = data[start_index:end_index]

        # Prepare the pagination details
        pagination_details = {
            "page": pagination_details["page"],
            "limit": pagination_details["limit"],
            "total_items": total_items,  # Use the original total count
        }

    # Convert data if it's a Pydantic model
    if isinstance(data, BaseModel):
        data = data.dict()
    elif isinstance(data, list) and all(isinstance(item, BaseModel) for item in data):
        data = [item.dict() for item in data]

    # Add `data` first
    response["data"] = data

    # Add `pagination` after `data`, if applicable
    if pagination_details:
        response["pagination"] = pagination_details

    return response
