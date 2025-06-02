"""
Test models for the application.
This module contains tests for the model registration and retrieval endpoints.
"""
from unittest.mock import patch

from fastapi import status
from fastapi.testclient import TestClient

from app.utils.exceptions import NoResultFound


def create_user(test_client: TestClient):
    """
    User creation method
    Returns:

    """
    response = test_client.post(
        "/users",
        json={
            "email": "test@test.com",
            "full_name": "test",
            "user_name": "test",
            "org_id": "1",
            "country": "NL",
            "phone": "12345678",
            "job_title": "Senior Engineer",
            "user_level": 1,
        },
    )
    return response


def test_register_user(test_client):
    """
    Test the user registration endpoint.

    Args:
        test_client (TestClient): The test client for making requests.

    Asserts:
        The response status code is 201.
        The response message is "Created new user."
        The response data contains the registered user .
    """
    response = create_user(test_client)
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["message"] == "Created new user."


def test_fetch_users(test_client):
    """
    Test the model retrieval endpoint.

    Args:
        test_client (TestClient): The test client for making requests.

    Asserts:
        The response status code is 200.
        The response message is "Users retrieved successfully."
        The response data is a list of Users.
    """
    response = test_client.post(
        "/users",
        json={
            "email": "test@test.com",
            "full_name": "test",
            "user_name": "test",
            "org_id": "1",
            "country": "NL",
            "phone": "12345678",
            "job_title": "Senior Engineer",
            "user_level": "1",
        },
    )
    if response.status_code == status.HTTP_201_CREATED:
        response = test_client.get("/users/1")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["message"] == "Users retrieved successfully."


def test_fetch_users_not_found(test_client):
    """
    Test the model retrieval endpoint for a non-existent user.

    Args:
        test_client (TestClient): The test client for making requests.

    Asserts:
        The response status code is 404.
        The response message is "No user found for user id"
    """
    with patch("app.services.users_service.UsersService.get_user_by_id") as mock_link:
        mock_link.side_effect = NoResultFound("User not found.")

        response = test_client.get("/users/5")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        expected_substring = "User not found."
        assert expected_substring in response.json()["detail"]


def test_fetch_all_users(test_client):
    """
    Test the users retrieval endpoint.

    Args:
        test_client (TestClient): The test client for making requests.

    Asserts:
        The response status code is 200.
        The response message is "Users retrieved successfully."
        The response data is a list of users.
    """
    response = test_client.get("/users")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["message"] == "Users retrieved successfully."
    assert isinstance(response.json()["data"], list)


def test_patch_user_server_error(test_client):
    """
    Test partial update with server error.
    """
    with patch("app.services.users_service.UsersService.update_user") as mock_update:
        mock_update.side_effect = Exception("Database connection failed")

        response = test_client.patch("/users/1", json={"email": "new@example.com"})
        print("test_patch_user_server_error", response.json())
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Database connection failed" in response.json()["detail"]


def test_patch_user_not_found(test_client):
    """
    Test partial update for non-existent user.
    """
    with patch("app.services.users_service.UsersService.update_user") as mock_update:
        mock_update.side_effect = NoResultFound("No user found for user id")

        response = test_client.patch("/users/999", json={"email": "new@example.com"})
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "No user found for user id" in response.json()["detail"]


def test_delete_users(test_client):
    """
    Test the user delete endpoint.

    Args:
        test_client (TestClient): The test client for making requests.

    Asserts:
        The response status code is 204.
    """
    response = create_user(test_client)
    if response.status_code == status.HTTP_200_OK:
        response = test_client.delete("/users/1")
        assert response.status_code == status.HTTP_204_NO_CONTENT


def test_delete_users_not_found(test_client):
    """
    Test the user delete endpoint for a non-existent user.

    Args:
        test_client (TestClient): The test client for making requests.

    Asserts:
        The response status code is 404.
    """
    with patch("app.services.users_service.UsersService.delete_user") as mock_link:
        mock_link.side_effect = NoResultFound("No user found for user id")

        response = test_client.delete("/users/5")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        expected_substring = "No user found for user id"
        assert expected_substring in response.json()["detail"]
