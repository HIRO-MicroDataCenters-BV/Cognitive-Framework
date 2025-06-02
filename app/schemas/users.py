"""
Users schema module.

This module defines the Pydantic models for representing user details in the application,
including the base model for user data and the configuration for ORM mapping.

Classes:
    UsersSchema: Pydantic model representing user details with optional attributes.
"""
import re
from datetime import datetime
from typing import Optional, Literal

from pydantic import BaseModel, Field, EmailStr, validator


class UserBase(BaseModel):
    """
    Base class for user request and update models.
    Contains shared validation logic for country and user_level.
    """

    user_level: Optional[int] = Field(
        default=0,
        description="Must be 0 or 1 or 2. " "0 - Free User , 1 - Paid User , 2-Admin",
        example=0,
    )
    country: Optional[str] = Field(min_length=2, max_length=2, example="US")

    @validator("user_level", pre=True, always=True)
    def validate_user_level(cls, value):
        """
        Validator function to validate user_level.
        It must be one of the allowed values: "0", "1", "2", "3".
        """
        allowed_values = {0, 1, 2, 3}
        if value not in allowed_values:
            raise ValueError(
                "Invalid user_level. Allowed values are: '0' (Junior), '1' (Intermediate), '2' (Senior). '3' (Expert)."
            )
        return value

    @validator("country")
    def validate_country(cls, value):
        """Validates that country is a valid two-letter uppercase country code."""
        if value:
            # Ensure that the country code is exactly two uppercase letters (ISO 3166-1 alpha-2)
            if not re.match(r"^[A-Z]{2}$", value):
                raise ValueError(
                    "Invalid country code. Must be a two-letter uppercase code like 'US', 'BE', 'NL'."
                )
        return value


class UsersSchema(BaseModel):
    """
    Pydantic model for user details.

    Attributes:
        id (Optional[int]): The unique identifier for the user.
        email (Optional[str]): The email address of the user.
        full_name (Optional[str]): The full name of the user.
        user_name (Optional[str]): The username of the user.
        org_id (Optional[int]): The ID of the organization the user belongs to.
        country (Optional[str]): The country of the user.
        phone (Optional[str]): The phone number of the user.
        job_title (Optional[str]): The job title of the user.
        user_level (Optional[int]): The user level (e.g., 0 - Free User , 1 - Paid User , 2-Admin).
        password_updated_at (Optional[datetime]): The last time the user's password was updated.
        created_at (Optional[datetime]): The timestamp when the user was created.
        updated_at (Optional[datetime]): The timestamp when the user was last updated.
    """

    id: Optional[int] = None
    email: Optional[str] = None
    full_name: Optional[str] = None
    user_name: Optional[str] = None
    org_id: Optional[int] = None
    country: Optional[str] = None
    phone: Optional[str] = None
    job_title: Optional[str] = None
    user_level: Optional[int] = None
    password_updated_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        """
        Configuration class for ORM and attribute handling.

        Attributes:
            orm_mode (Literal[True]): Enables ORM mode for Pydantic models, allowing attribute access similar
            to ORM objects.
            from_attributes (Literal[True]): Enables model creation from attributes, useful for ORM integrations.
            arbitrary_types_allowed (bool): Allows arbitrary types in Pydantic models.
        """

        orm_mode: Literal[True] = True
        from_attributes: Literal[True] = True
        arbitrary_types_allowed = True


class UsersRequest(UserBase):
    """
    Pydantic model for user details on user creation.

    Attributes:
        email (Optional[str]): The email address of the user.
        full_name (Optional[str]): The full name of the user.
        user_name (Optional[str]): The username of the user. 3-20 characters, alphanumeric
        org_id (Optional[int]): The ID of the organization the user belongs to.
        country (Optional[str]): The country of the user.
        phone (Optional[str]): The phone number of the user.
        job_title (Optional[str]): The job title of the user.
        user_level (Optional[int]): The user level (e.g., admin, user). Defaults to '0'
    """

    email: Optional[EmailStr] = Field(..., example="user@example.com")
    user_name: Optional[str] = Field(
        ..., min_length=3, max_length=20, regex="^[a-zA-Z0-9_]+$", example="john_doe123"
    )

    org_id: Optional[int] = Field(gt=0, example=1)
    full_name: Optional[str] = Field(
        None, min_length=2, max_length=100, example="John Doe"
    )
    phone: Optional[str] = Field(
        None, regex=r"^\+?[1-9]\d{1,14}$", example="+1234567890"
    )
    job_title: Optional[str] = Field(None, example="analyst")


class UsersUpdateRequest(UserBase):
    """
    Pydantic model for updating user details.

    Attributes:
        email (Optional[str]): The email address of the user.
        full_name (Optional[str]): The full name of the user.
        user_name (Optional[str]): The username of the user. 3-20 characters, alphanumeric
        org_id (Optional[int]): The ID of the organization the user belongs to.
        country (Optional[str]): The country of the user.
        phone (Optional[str]): The phone number of the user.
        job_title (Optional[str]): The job title of the user.
        user_level (Optional[int]): The user level (e.g., admin, user). Defaults to '0'
    """

    email: Optional[EmailStr] = Field(None, example="user@example.com")
    user_name: Optional[str] = Field(
        None,
        min_length=3,
        max_length=20,
        regex="^[a-zA-Z0-9_]+$",
        example="john_doe123",
    )

    org_id: Optional[int] = Field(None, gt=0, example=1)

    full_name: Optional[str] = Field(
        None, min_length=2, max_length=100, example="John Doe"
    )
    phone: Optional[str] = Field(
        None, regex=r"^\+?[1-9]\d{1,14}$", example="+1234567890"
    )
    job_title: Optional[str] = Field(None, example="analyst")
    updated_at: datetime = datetime.utcnow()
