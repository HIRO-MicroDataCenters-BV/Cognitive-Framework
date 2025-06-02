"""
Custom exception classes for the application.

This module defines custom exception classes for handling various error scenarios in the application.

Classes:
    NotFoundException: Raised when a requested resource is not found.
    ValidationException: Raised when there is a validation error.
    UnauthorizedException: Raised when there is an unauthorized access attempt.
    ConflictException: Raised when there is a conflict error.
    OperationException: Raised when there is an operation error.
"""
from typing import Optional, Union, List, Any, Dict

from sqlalchemy.exc import (
    DatabaseError,
    NoResultFound as SQLAlchemyNoResultFound,
    SQLAlchemyError,
)


class NotFoundException(Exception):
    """
    Exception raised when a requested resource is not found.

    Attributes:
        message (str): The error message.
    """

    def __init__(self, message: str = "Resource not found"):
        self.message = message
        super().__init__(self.message)


class ValidationException(Exception):
    """
    Exception raised when there is a validation error.

    Attributes:
        message (str): The error message.
    """

    def __init__(self, message: str = "Validation error"):
        self.message = message
        super().__init__(self.message)


class UnauthorizedException(Exception):
    """
    Exception raised when there is an unauthorized access attempt.

    Attributes:
        message (str): The error message.
    """

    def __init__(self, message: str = "Unauthorized access"):
        self.message = message
        super().__init__(self.message)


class ConflictException(Exception):
    """
    Exception raised when there is a conflict error.

    Attributes:
        message (str): The error message.
    """

    def __init__(self, message: str = "Conflict error"):
        self.message = message
        super().__init__(self.message)


class OperationException(Exception):
    """
    Exception raised when there is an operation error.

    Attributes:
        message (str): The error message.
    """

    def __init__(self, message: str = "Operation error"):
        self.message = message
        super().__init__(self.message)


class NoResultFound(SQLAlchemyNoResultFound):
    """Custom exception to handle cases where no result is found."""

    def __init__(self, message: str = "No Result Found"):
        self.message = message
        super().__init__(self.message)


class ModelNotFoundException(Exception):
    """Exception raised when no model is found in the database."""

    def __init__(self, message="Model Not Found") -> None:
        self.message = message
        super().__init__(self.message)


class ModelFileExistsException(Exception):
    """
    Exception class related to Model Exists
    """

    def __init__(self, message="Model File Exits") -> None:
        self.message = message
        super().__init__(self.message)


class InvalidDurationException(Exception):
    """
    Exception class related to duration
    """

    def __init__(self, message="Invalid duration") -> None:
        self.message = message
        super().__init__(self.message)


class InvalidValueException(Exception):
    """
    Exception class related to value
    """

    def __init__(self, message="Negative value not allowed") -> None:
        self.message = message
        super().__init__(self.message)


class DatasetNotFoundException(Exception):
    """
    Exception class related to Dataset not found
    """

    def __init__(self, message="Dataset not found") -> None:
        self.message = message
        super().__init__(self.message)


class DatasetUploadExistsException(Exception):
    """
    Exception class related to Dataset upload already exist
    """

    def __init__(self, message="Dataset upload already exist") -> None:
        self.message = message
        super().__init__(self.message)


class DatasetTableExistsException(Exception):
    """
    Exception class related to Dataset Table already exists
    """

    def __init__(self, message="Dataset Table already exists") -> None:
        self.message = message
        super().__init__(self.message)


class ModelFileNotFoundException(Exception):
    """
    Exception class related to Model Exists
    """

    def __init__(self, message="Model File Not Found") -> None:
        self.message = message
        super().__init__(self.message)


class NoMessagesFound(Exception):
    """
    Exception class related to No Topic data exists
    """

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class IntegrityError(DatabaseError):
    """
    Exception class related to Database Integrity Error
    """

    def __init__(
        self,
        *args,
        message="Database Integrity Error",
        orig: Optional[BaseException] = None,
        params: Optional[Union[List[Any], Dict[Any, Any]]] = None,
        **kwargs
    ) -> None:
        super().__init__(message, params=params, orig=orig)
        self.message = message
        self.orig = orig


class MinioClientError(Exception):
    """
    Exception class related to Database Integrity Error
    """

    def __init__(self, message="Minio client error") -> None:
        self.message = message
        super().__init__(self.message)


class DatabaseException(SQLAlchemyError):
    """
    Exception class related to Database Integrity Error
    """

    def __init__(self, message="Database Error") -> None:
        super().__init__(message)
        self.message = message
