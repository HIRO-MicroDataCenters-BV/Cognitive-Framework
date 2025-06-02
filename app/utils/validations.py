"""
Validation utility functions.

This module provides utility functions for validating various types of data.

Functions:
    validate_positive_int: Validates that an integer is positive.
    validate_non_empty_string: Validates that a string is non-empty.
"""

from app.utils.exceptions import ValidationException


def validate_positive_int(value: int) -> int:
    """
    Validate that the given integer is positive.

    Args:
        value (int): The integer to validate.

    Returns:
        int: The validated positive integer.

    Raises:
        ValidationException: If the integer is not positive.
    """
    if value <= 0:
        raise ValidationException("Value must be a positive integer")
    return value


def validate_non_empty_string(value: str) -> str:
    """
    Validate that the given string is non-empty.

    Args:
        value (str): The string to validate.

    Returns:
        str: The validated non-empty string.

    Raises:
        ValidationException: If the string is empty or contains only whitespace.
    """
    if not value or not value.strip():
        raise ValidationException("String must be non-empty")
    return value
