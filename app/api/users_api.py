"""
API endpoints for managing users.

This module provides endpoints for registering new users and retrieving existing users.
"""
from typing import List

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    Path,
)
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.response import StandardResponse
from app.schemas.users import UsersSchema, UsersRequest, UsersUpdateRequest
from app.services.users_service import UsersService
from app.utils.exceptions import NoResultFound, OperationException
from app.utils.response_utils import standard_response

router = APIRouter()


@router.post(
    "/users",
    response_model=StandardResponse[UsersSchema],
    status_code=status.HTTP_201_CREATED,
)
async def register_user(user: UsersRequest, db_app: Session = Depends(get_db)):
    """
    API route to create a new user.

    This endpoint allows you to create a new user by providing user details.

    **Parameters:**
    - **Required Fields**:
        - `email`: Valid email address (e.g., user@example.com)
        - `user_name`: 3-20 characters, alphanumeric with underscores
    - **Optional Fields with Defaults**:
        - `user_level`: User level '0' (Junior), '1' (Intermediate), '2' (Senior). '3' (Expert).
        - `country`: country name
        - `org_id`: Organization ID (default: 1)
    - **Other Optional Fields**:
        - `full_name`: 2-100 characters
        - `phone`: E.164 format phone number
        - `job_title`: Free-text job description
    - `db_app` (Session):
        The database session, automatically provided by FastAPI's dependency injection.

    **Behavior:**
    - StandardResponse[UsersSchema]: The standard response containing the registered model information.
    - Handles exceptions and raises an `HTTPException` with status code 500 for any internal errors.

    **Responses:**
    - **201 OK**: Returns the newly created user details.
    - **400 Bad Request**: Raised if an operational error occurs.
    - **500 Internal Server Error**: Raised if an unexpected error occurs.
    """
    service = UsersService(db_app)
    try:
        data = service.create_user(user)
        return standard_response(
            status_code=status.HTTP_201_CREATED, message="Created new user.", data=data
        )
    except OperationException as exp:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exp))
    except Exception as exp:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal Server Error: {str(exp)}",
        )


@router.get("/users/{id}")
def fetch_user(
    id: int = Path(..., gt=0, description="The ID of the user"),
    db_app: Session = Depends(get_db),
):
    # pylint: disable=invalid-name,redefined-builtin
    """
    API route to retrieve a user by their ID.

    This endpoint allows you to fetch a user by providing their unique ID.

    **Parameters:**
    - `id` (int):
        The ID of the user to retrieve.
    - `db_app` (Session):
        The database session, automatically provided by FastAPI's dependency injection.

    **Behavior:**
    - Returns the user details upon success.
    - Handles exceptions and raises appropriate `HTTPException` responses for errors.

    **Responses:**
    - **200 OK**: Returns the user details.
    - **404 Not Found**: Raised if no user is found with the given ID.
    - **500 Internal Server Error**: Raised if an unexpected error occurs.
    """
    service = UsersService(db_app)
    try:
        data = service.get_user_by_id(id)
        return standard_response(
            status_code=status.HTTP_200_OK,
            message="Users retrieved successfully.",
            data=data,
        )
    except NoResultFound as exp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"{exp.message}"
        )
    except Exception as exp:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal Server Error: {str(exp)}",
        )


@router.get("/users", response_model=StandardResponse[List[UsersSchema]])
def fetch_users(db_app: Session = Depends(get_db)):
    """
    API route to retrieve all users.

    This endpoint fetches a list of all registered users.

    **Parameters:**
    - `db_app` (Session):
        The database session, automatically provided by FastAPI's dependency injection.

    **Behavior:**
    - Returns a list of users upon success.
    - Handles exceptions and raises appropriate `HTTPException` responses for errors.

    **Responses:**
    - **200 OK**: Returns a list of users with a success message.
    - **500 Internal Server Error**: Raised if an unexpected error occurs.
    """
    service = UsersService(db_app)
    try:
        data: List[UsersSchema] = service.get_users()
        return standard_response(
            status_code=status.HTTP_200_OK,
            message="Users retrieved successfully.",
            data=data,
        )
    except Exception as exp:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal Server Error: {str(exp)}",
        )


@router.patch("/users/{id}", response_model=StandardResponse[UsersSchema])
def update_user(id: int, user: UsersUpdateRequest, db_app: Session = Depends(get_db)):
    # pylint: disable=invalid-name,redefined-builtin
    """
    API route to update an existing user.

    This endpoint allows updating a user's details by providing their ID and new data.

    **Parameters:**
    - `id` (int):
        The ID of the user to update.
    - `user` (UsersSchema):
        The updated user data.
        - **Required Fields**:
            - `email`: Valid email address (e.g., user@example.com)
            - `user_name`: 3-20 characters, alphanumeric with underscores
        - **Optional Fields with Defaults**:
            - `user_level`: User level '0' (Junior), '1' (Intermediate), '2' (Senior). '3' (Expert).
            - `country`: country name
            - `org_id`: Organization ID (default: 1)
        - **Other Optional Fields**:
            - `full_name`: 2-100 characters
            - `phone`: E.164 format phone number
            - `job_title`: Free-text job description
    - `db_app` (Session):
        The database session, automatically provided by FastAPI's dependency injection.

    **Behavior:**
    - Updates the user details upon success and returns the updated user.
    - Handles exceptions and raises appropriate `HTTPException` responses for errors.

    **Responses:**
    - **200 OK**: Returns the updated user details.
    - **404 Not Found**: Raised if no user is found with the given ID.
    - **400 Bad Request**: Raised if validation fails.
    - **500 Internal Server Error**: Raised if an unexpected error occurs.
    """
    service = UsersService(db_app)

    try:
        data = service.update_user(id, user)
        return standard_response(
            status_code=status.HTTP_200_OK,
            message="User updated successfully.",
            data=data,
        )
    except NoResultFound as exp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exp))
    except ValidationError as exp:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exp)
        )
    except Exception as exp:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal Server Error: {str(exp)}",
        )


@router.delete("/users/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    id: int = Path(..., gt=0, description="The ID of the user"),
    db_app: Session = Depends(get_db),
):
    # pylint: disable=invalid-name,redefined-builtin
    """
    API route to delete a user by their ID.

    This endpoint allows you to delete a user by providing their unique ID.

    **Parameters:**
    - `id` (int):
        The ID of the user to delete.
    - `db_app` (Session):
        The database session, automatically provided by FastAPI's dependency injection.

    **Behavior:**
    - Deletes the user upon success and returns a confirmation message.
    - Handles exceptions and raises appropriate `HTTPException` responses for errors.

    **Responses:**
    - **200 OK**: User successfully deleted, returns a confirmation message.
    - **404 Not Found**: Raised if no user is found with the given ID.
    - **500 Internal Server Error**: Raised if an unexpected error occurs.
    """
    service = UsersService(db_app)
    try:
        service.delete_user(id)
    except NoResultFound as exp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exp))
    except Exception as exp:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal Server Error: {str(exp)}",
        )
