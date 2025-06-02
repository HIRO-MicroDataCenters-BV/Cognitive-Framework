"""
Service for registering and retrieving user information.

This module provides a service class for registering new users and retrieving existing users from the database.
"""

from datetime import datetime
from typing import List, Optional

from sqlalchemy.exc import IntegrityError as DBIntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session
from sqlalchemy.exc import NoResultFound as NoRowFound

from app.middleware.logger import logger
from app.models import Users
from app.schemas.users import UsersSchema, UsersRequest, UsersUpdateRequest
from app.utils.exceptions import NoResultFound, OperationException

log = logger()


class UsersService:
    """
    Service class for registering and retrieving users information.
    """

    def __init__(self, db_app: Session):
        """
            Initialize the service with a database session and configuration.

        Args:
                db_app (Session): The database session.
        """
        self.db_app = db_app

    def get_users(self) -> List[UsersSchema]:
        """
        Retrieves all users from the database.

        Returns:
            List[UsersSchema]: A list of user schema objects retrieved from the database.

        Raises:
            OperationException: If a database-related error occurs during the query, an `OperationException`
                            is raised with a detailed error message.
            Exception: If an unexpected error occurs, the exception is logged and raised again for further handling.
        """
        try:
            result = self.db_app.query(Users).all()
            if not result:
                log.debug("No users found in the database.")
            return result
        except SQLAlchemyError as exp:
            raise OperationException(f"Database error: {str(exp)}")
        except Exception as exp:
            log.error("Unable to retrieve users %s", str(exp), exc_info=True)
            raise exp

    def get_user_by_id(self, user_id: int) -> Optional[UsersSchema]:
        """
        Retrieves a user by their ID from the database.

        Args:
            user_id (int): The ID of the user to retrieve.

        Returns:
            Optional[UsersSchema]: A `UsersSchema` object representing the user if found. If no user
                                    is found for the provided `user_id`, `None` is returned.

        Raises:
            NoResultFound: If no user is found with the specified `user_id`, this exception is raised.
            OperationException: If a database-related error occurs during the query, an `OperationException`
                                 is raised with the error message.
            Exception: If an unexpected error occurs, it is logged and raised again for further handling.
        """
        try:
            user = self.db_app.query(Users).filter(Users.id == user_id).one()
            return UsersSchema.from_orm(user)
        except NoRowFound as exp:
            log.error(
                "User not found for the id %s %s",
                user_id,
                str(exp),
                exc_info=True,
            )
            raise NoResultFound(f"No user found for user id : {user_id}")
        except SQLAlchemyError as exp:
            raise OperationException(f"Database error: {str(exp)}")
        except Exception as exp:
            log.error("Unable to get user %s", str(exp), exc_info=True)
            raise exp

    def create_user(self, user: UsersRequest) -> UsersSchema:
        """
        Creates a new user in the database.

        Args:
            user (UsersSchema): The user data to create, represented as a `UsersSchema` object.

        Returns:
            UsersSchema: A `UsersSchema` object representing the created user, populated with the data
                          from the database after the commit.

        Raises:
            OperationException: If a database-related error occurs (e.g., integrity constraint violation).
            Exception: If an unexpected error occurs during the user creation process, it is logged and raised again.
        """
        try:
            db_user = Users(
                email=user.email,
                full_name=user.full_name,
                user_name=user.user_name,
                org_id=user.org_id,
                country=user.country,
                phone=user.phone,
                job_title=user.job_title,
                user_level=user.user_level,
                password_updated_at=datetime.utcnow(),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )

            self.db_app.add(db_user)
            self.db_app.commit()
            log.info("User created successfully: %s", user)
            return UsersSchema.from_orm(db_user)
        except DBIntegrityError as exc:
            self.db_app.rollback()
            raise OperationException(f"Database error: {str(exc)}")
        except Exception as exp:
            self.db_app.rollback()
            log.error("Unable to create User %s", str(exp), exc_info=True)
            raise exp

    def update_user(
        self, user_id: int, user_data: UsersUpdateRequest
    ) -> Optional[UsersSchema]:
        """
        Updates an existing user's information in the database.

        Args:
            user_id (int): The ID of the user to update.
            user_data (UsersSchema): The new data for the user to update, represented as a `UsersSchema` object.

        Returns:
            Optional[UsersSchema]: A `UsersSchema` object representing the updated user, or `None` if the user
                                    was not found or updated.

        Raises:
            NoResultFound: If no user is found with the specified `user_id`.
            Exception: If an unexpected error occurs during the user update process, it is logged and raised again.
        """
        try:
            user = self.db_app.query(Users).filter(Users.id == user_id).one()
            for key, value in user_data.dict().items():
                if value is not None:  # Only update non-null fields
                    setattr(user, key, value)
            self.db_app.commit()
            log.info("User Information updated successfully: %s", user)
            return UsersSchema.from_orm(user)

        except NoRowFound as exp:
            log.error(
                "User not found for the id %s %s",
                user_id,
                str(exp),
                exc_info=True,
            )
            raise NoResultFound(f"No user found for user id : {user_id}")

        except Exception as exp:
            log.error(
                "Exception occurred during user update for the user id %s %s ",
                user_id,
                str(exp),
                exc_info=True,
            )
            raise exp

    def delete_user(self, user_id: int):
        """
        Deletes a user from the database by their ID.

        Args:
            user_id (int): The ID of the user to delete.

        Raises:
            NoResultFound: If no user is found with the specified `user_id`, this exception is raised.
            Exception: If an unexpected error occurs during the deletion process, it is logged and raised again.
        """
        try:
            user = self.db_app.query(Users).filter(Users.id == user_id).one()
            self.db_app.delete(user)
            self.db_app.commit()
            log.info("User id %s deleted successfully.", user_id)

        except NoRowFound as exp:
            log.error(
                "User not found for the id %s %s",
                user_id,
                str(exp),
                exc_info=True,
            )
            raise NoResultFound(f"No user found for user id : {user_id}")

        except Exception as exp:
            self.db_app.rollback()
            log.error(
                "Exception occurred during user deleting of user id %s %s ",
                user_id,
                str(exp),
                exc_info=True,
            )
            raise exp
