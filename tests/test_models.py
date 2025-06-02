"""
Test models for the application.
This module contains tests for the model registration and retrieval endpoints.
"""

import io
from datetime import datetime
from unittest.mock import patch
from fastapi import status
from fastapi.testclient import TestClient
from starlette.responses import StreamingResponse

from app.schemas.model_info import ModelInfo
from app.utils.exceptions import (
    ModelNotFoundException,
    ModelFileExistsException,
    NoResultFound,
    OperationException,
    MinioClientError,
)
from config import constants as const


def test_register_model(test_client) -> None:
    """
    Test the model registration endpoint.

    Args:
        test_client (TestClient): The test client for making requests.

    Asserts:
        The response status code is 201.
        The response message is "Created new model."
        The response data contains the registered model name.
    """
    response = test_client.post(
        "/models",
        json={
            "name": "test_model",
            "version": 1,
            "type": "test",
            "description": "A test model",
        },
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["message"] == "Created new model."
    assert response.json()["data"]["name"] == "test_model"


def test_get_models(test_client) -> None:
    """
    Test the model retrieval endpoint.

    Args:
        test_client (TestClient): The test client for making requests.

    Asserts:
        The response status code is 200.
        The response message is "Models retrieved successfully."
        The response data is a list of models.
    """
    response = test_client.get("/models")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["message"] == "Models retrieved successfully."
    assert isinstance(response.json()["data"], list)


def test_get_models_pagination(test_client) -> None:
    """
    Test the model retrieval endpoint.

    Args:
        test_client (TestClient): The test client for making requests.

    Asserts:
        The response status code is 200.
        The response message is "Models retrieved successfully."
        The response data is a list of models.
    """
    limit = 3
    page_size = 1
    response = test_client.get(f"/models?page={page_size}&limit={limit}")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["message"] == "Models retrieved successfully."
    assert isinstance(response.json()["data"], list)
    assert len(response.json()["data"]) <= limit


def test_delete_model(test_client) -> None:
    """
    Test the model deletion endpoint.

    Args:
        test_client (TestClient): The test client for making requests.

    Asserts:
        The response status code is 200.
        The response message is "Model deleted successfully."
        The response data contains the deleted model ID.
    """
    # First, create a model to delete
    response = test_client.post(
        "/models",
        json={
            "name": "test_model_to_delete",
            "version": 1,
            "type": "test",
            "description": "A test model to delete",
        },
    )
    print("test_delete_model", response.json())
    model_id = response.json()["data"]["id"]
    # Now, delete the model
    response = test_client.delete(f"/models/{model_id}")
    assert response.status_code == status.HTTP_204_NO_CONTENT

    # Try to delete the same model again to test failure scenario
    response = test_client.delete(f"/models/{model_id}")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == f"Model with ID {model_id} not found."


def test_update_model(test_client) -> None:
    """
    Test the model update endpoint.

    Args:
        test_client (TestClient): The test client for making requests.

    Asserts:
        The response status code is 200.
        The response message is "Model updated successfully."
        The response data contains the updated model information.
    """
    # First, create a model to update
    response = test_client.post(
        "/models",
        json={
            "name": "test_model_to_update",
            "version": 1,
            "type": "test",
            "description": "A test model to update",
        },
    )
    print("test_update_model", response.json())
    model_id = response.json()["data"]["id"]
    # Now, update the model
    response = test_client.patch(
        f"/models/{model_id}",
        json={
            "name": "updated_test_model",
            "version": 2,
            "type": "test",
            "description": "An updated test model",
        },
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["message"] == "Model updated successfully."
    assert response.json()["data"]["name"] == "updated_test_model"
    assert response.json()["data"]["version"] == 2


def test_update_nonexistent_model(test_client) -> None:
    """
    Test the model update endpoint with a non-existent model ID.

    This test specifically checks the behavior when attempting to update a model
    that doesn't exist in the database (ID 9999).

    Args:
        test_client (TestClient): The test client for making requests.

    Asserts:
        The response status code is 404 (Not Found).
        The response contains the appropriate error message.
    """
    response = test_client.patch(
        "/models/9999",
        json={
            "name": "non_existent_model",
            "version": 1,
            "type": "test",
            "description": "A non-existent model",
        },
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Model with ID 9999 not found."


def test_update_model_empty_payload(test_client) -> None:
    """
    Test the model update endpoint with an empty JSON payload.

    This test verifies that when an empty JSON payload is provided,
    the model remains unchanged and the API returns a 200 OK status.

    Args:
        test_client (TestClient): The test client for making requests.

    Asserts:
        The response status code is 200 (OK).
        The response message indicates successful update.
        The model data remains unchanged.
    """
    # First, create a model to update
    response = test_client.post(
        "/models",
        json={
            "name": "test_model_empty_update",
            "version": 1,
            "type": "test",
            "description": "A test model for empty update",
        },
    )
    model_id = response.json()["data"]["id"]

    # Get the initial model data
    initial_model = response.json()["data"]

    # Update the model with an empty JSON payload
    response = test_client.patch(
        f"/models/{model_id}",
        json={},
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["message"] == "Model updated successfully."

    # Verify that the model data remains unchanged
    updated_model = response.json()["data"]
    assert updated_model["name"] == initial_model["name"]
    assert updated_model["version"] == initial_model["version"]
    assert updated_model["type"] == initial_model["type"]
    assert updated_model["description"] == initial_model["description"]


def test_update_model_partial_payload(test_client) -> None:
    """
    Test the model update endpoint with a partial JSON payload.

    This test verifies that when only some fields are provided in the update payload,
    only those fields are updated while the others remain unchanged.

    Args:
        test_client (TestClient): The test client for making requests.

    Asserts:
        The response status code is 200 (OK).
        The response message indicates successful update.
        Only the specified fields are updated.
    """
    # First, create a model to update
    response = test_client.post(
        "/models",
        json={
            "name": "test_model_partial_update",
            "version": 1,
            "type": "test",
            "description": "A test model for partial update",
        },
    )
    model_id = response.json()["data"]["id"]

    # Update the model with a partial JSON payload (only name and description)
    response = test_client.patch(
        f"/models/{model_id}",
        json={
            "name": "partially_updated_model",
            "description": "A partially updated model",
        },
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["message"] == "Model updated successfully."

    # Verify that only the specified fields are updated
    updated_model = response.json()["data"]
    assert updated_model["name"] == "partially_updated_model"
    assert updated_model["version"] == 1
    assert updated_model["type"] == "test"
    assert updated_model["description"] == "A partially updated model"


def register_model_file(test_client: TestClient, mock_getenv, model_name):
    """
    Helper function to post the model file details .

    Args:
       test_client (TestClient): The test client for making requests.

    Asserts:
            The response status code is 201.
            The response content will have model file details.
    """

    response = test_client.post(
        "/models",
        json={
            "name": model_name,
            "version": 1,
            "register_user_id": 1,
            "type": "test",
            "description": "A test detailed model",
        },
    )
    result = response.json()
    file_name = const.TEST_FILE_NAME
    file_content = io.BytesIO(b"this is a test")
    files = {"files": (file_name, file_content)}
    data = {
        "model_id": result["data"]["id"],
        "file_description": "model policy file",
        "file_type": 0,
    }
    if result["status_code"] == status.HTTP_201_CREATED:
        with patch(
            "app.services.model_register_service.cogflow.save_to_minio"
        ) as mock_upload:
            mock_upload.return_value = True

            file_response = test_client.post("/models/file", data=data, files=files)
            return file_response.json()


def test_upload_model_file(test_client) -> None:
    """
    Test the model file upload endpoint.

    Args:
        test_client (TestClient): The test client for making requests.

    Asserts:
        The response status code is 201.
        The response message is "File uploaded successfully."
        The response data contains the registered model file details.
    """
    file_name = const.TEST_FILE_NAME
    model_id = 1
    file_content = io.BytesIO(b"this is a test")
    data = {
        "model_id": 1,
        "file_description": "model policy file",
        "file_type": 0,
    }
    files = {"files": (file_name, file_content)}
    with patch(
        "app.services.model_register_service.ModelRegisterService.upload_model_file"
    ) as mock_upload:
        mock_upload.return_value = {
            "id": 1,
            "model_id": 1,
            "register_date": "2023-10-01T00:00:00",
            "file_name": file_name,
            "file_path": "s3://bucket_name/path/to/file",
            "file_type": 0,
            "file_description": "model policy file",
        }

        response = test_client.post(f"/models/{model_id}/file", data=data, files=files)

        response_data = response.json()
        assert response.status_code == status.HTTP_201_CREATED
        assert response_data["message"] == "File uploaded successfully."
        assert "data" in response_data
        assert response_data["data"]["file_name"] == file_name
        assert response_data["data"]["file_path"] == "s3://bucket_name/path/to/file"
        assert response_data["data"]["model_id"] == 1
        assert response_data["data"]["register_date"] == "2023-10-01T00:00:00"
        assert response_data["data"]["file_type"] == 0
        assert response_data["data"]["id"] == 1


def test_upload_model_file_empty_file(test_client) -> None:
    """
    Test the model file upload endpoint with an empty file.

    Args:
        test_client (TestClient): The test client for making requests.

    Asserts:
        The response status code is 422.
        The response detail contains the error message about empty files.
    """
    model_id = 1
    data = {
        "file_description": "model policy file",
        "file_type": 0,
    }
    # Empty file
    files = {"files": ("", io.BytesIO(b""))}

    response = test_client.post(f"/models/{model_id}/file", data=data, files=files)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    response_json = response.json()
    assert "detail" in response_json
    assert "field required" in response_json["detail"][0]["msg"]


def test_upload_model_file_model_not_found(test_client) -> None:
    """
    Test the model file upload endpoint with a non-existent model ID.

    Args:
        test_client (TestClient): The test client for making requests.

    Asserts:
        The response status code is 404.
        The response detail contains the error message about model not found.
    """
    model_id = 1111
    file_name = const.TEST_FILE_NAME
    file_content = io.BytesIO(b"this is a test")
    data = {
        "file_description": "model policy file",
        "file_type": 0,
    }
    files = {"files": (file_name, file_content)}

    with patch(
        "app.services.model_register_service.ModelRegisterService.upload_model_file"
    ) as mock_upload:
        mock_upload.side_effect = NoResultFound("No Model Id Found")

        response = test_client.post(f"/models/{model_id}/file", data=data, files=files)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "No Model Id found" in response.json()["detail"]


def test_upload_model_file_exists(test_client, mock_getenv):
    """
    Test the model file upload endpoint.

    Args:
        test_client (TestClient): The test client for making requests.

    Asserts:
        The response status code is 409.
        The response message is "Model File already exists"
    """
    file_name = const.TEST_FILE_NAME
    model_id = 2
    file_content = io.BytesIO(b"this is a test")
    data = {
        "model_id": 2,
        "file_description": "model policy file",
        "file_type": 1,
    }
    files = {"files": (file_name, file_content)}
    with patch(
        "app.services.model_register_service.ModelRegisterService.upload_model_file"
    ) as mock_upload:
        mock_upload.side_effect = OperationException(
            "Operational_error{unexpected error: (psycopg2.errors.UniqueViolation) "
            'duplicate key value violates unique constraint "unique_filename_per_user_per_model"}'
        )
        response = test_client.post(f"/models/{model_id}/file", data=data, files=files)
        response_data = response.json()
        expected_substring = "Model File already exists"
        assert expected_substring in response_data["detail"]
        assert response.status_code == status.HTTP_409_CONFLICT


def test_upload_file_client_error(test_client, mock_getenv):
    """
    Test the model file upload endpoint for MinIO connection error.

    Args:
        test_client (TestClient): The test client for making requests.

    Asserts:
        The response status code is 404.
        The response message contains "MinioClient Error:".
    """
    file_name = const.TEST_FILE_NAME
    model_id = 1
    file_content = io.BytesIO(b"this is a test")
    data = {
        "model_id": 2,
        "file_description": "model policy file",
        "file_type": 0,
    }
    files = {"files": (file_name, file_content)}

    with patch(
        "app.services.model_register_service.ModelRegisterService.upload_model_file"
    ) as mock_upload:
        mock_upload.side_effect = MinioClientError("MinioClient Error")

        response = test_client.post(f"/models/{model_id}/file", data=data, files=files)

        response_data = response.json()
        expected_substring = "MinioClient Error:"

        # Assert the response JSON 'detail' field contains the expected substring
        assert expected_substring in response_data["detail"]

        # Assert the response status code is 404
        assert response.status_code == status.HTTP_404_NOT_FOUND


def test_update_model_file(test_client, mock_getenv) -> None:
    """
    Test the model file update endpoint.

    Args:
        test_client (TestClient): The test client for making requests.

    Asserts:
        The response status code is 201.
        The response message is "File updated successfully."
        The response data contains the registered model file details.
    """
    file_name = const.TEST_FILE_NAME
    file_content = io.BytesIO(b"this is a test")
    data = {"model_id": 2, "file_id": 1, "file_description": "model policy file"}
    files = {"files": (file_name, file_content)}

    with patch(
        "app.services.model_register_service.ModelRegisterService.update_model_file"
    ) as mock_upload:
        mock_upload.return_value = {
            "id": 1,
            "model_id": 2,
            "register_date": "2023-10-01T00:00:00",
            "file_name": file_name,
            "file_path": "s3://bucket_name/path/to/file",
            "file_type": 0,
            "file_description": "model policy file",
        }

        response = test_client.put("/models/file/version", data=data, files=files)

        response_data = response.json()
        assert response.status_code == status.HTTP_200_OK
        assert response_data["message"] == "File updated successfully."
        assert "data" in response_data
        assert response_data["data"]["file_name"] == file_name
        assert response_data["data"]["file_path"] == "s3://bucket_name/path/to/file"
        assert response_data["data"]["model_id"] == 2
        assert response_data["data"]["register_date"] == "2023-10-01T00:00:00"
        assert response_data["data"]["file_type"] == 0
        assert response_data["data"]["id"] == 1


def test_update_model_file_client_error(test_client, mock_getenv) -> None:
    """
    Test the model file update endpoint for handling a client error.

    Args:
        test_client (TestClient): The test client for making requests.

    Asserts:
        The response status code is 404.
        The response message contains "MinioClient Error:".
    """
    file_name = const.TEST_FILE_NAME
    file_content = io.BytesIO(b"this is a test")
    data = {"model_id": 2, "file_id": 1, "file_description": "model policy file"}
    files = {"files": (file_name, file_content)}

    with patch(
        "app.services.model_register_service.ModelRegisterService.update_model_file"
    ) as mock_upload:
        # Simulate a MinIO ClientError
        mock_upload.side_effect = MinioClientError("MinioClient Error")

        response = test_client.put("/models/file/version", data=data, files=files)

        response_data = response.json()
        expected_substring = "MinioClient Error:"

        # Assert the response JSON 'detail' field contains the expected substring
        assert expected_substring in response_data["detail"]

        # Assert the response status code is 404
        assert response.status_code == status.HTTP_404_NOT_FOUND


def test_update_model_file_integrity_error(test_client, mock_getenv) -> None:
    """
    Test the model file update endpoint for handling an IntegrityError.

    Args:
        test_client (TestClient): The test client for making requests.

    Asserts:
        The response status code is 409.
        The response message contains "IntegrityError:".
    """
    file_name = const.TEST_FILE_NAME
    file_content = io.BytesIO(b"this is a test")
    data = {"model_id": 2, "file_id": 1, "file_description": "model policy file"}
    files = {"files": (file_name, file_content)}

    with patch(
        "app.services.model_register_service.ModelRegisterService.update_model_file"
    ) as mock_upload:
        mock_upload.side_effect = ModelFileExistsException("Model File already exists.")

        response = test_client.put("/models/file/version", data=data, files=files)

        response_data = response.json()
        expected_substring = "ModelFileExistsException"

        # Assert the response JSON 'detail' field contains the expected substring
        assert expected_substring in response_data["detail"]

        # Assert the response status code is 409 (Conflict)
        assert response.status_code == status.HTTP_409_CONFLICT


def test_update_model_file_model_not_found(test_client, mock_getenv) -> None:
    """
    Test the model file update endpoint for handling a ModelNotFoundException.

    Args:
        test_client (TestClient): The test client for making requests.

    Asserts:
        The response status code is 404.
        The response message contains "Model Id Not Found.".
    """
    file_name = const.TEST_FILE_NAME
    file_content = io.BytesIO(b"this is a test")
    data = {
        "model_id": 10,
        "file_id": 1,
        "file_description": "model policy file",
    }
    files = {"files": (file_name, file_content)}

    with patch(
        "app.services.model_register_service.ModelRegisterService.update_model_file"
    ) as mock_upload:
        # Simulate a ModelNotFoundException
        mock_upload.side_effect = ModelNotFoundException("Model Id Not Found.")

        response = test_client.put("/models/file/version", data=data, files=files)

        response_data = response.json()
        expected_substring = "Model Id Not Found."

        # Assert the response JSON 'detail' field contains the expected substring
        assert expected_substring in response_data["detail"]

        # Assert the response status code is 404 (Not Found)
        assert response.status_code == status.HTTP_404_NOT_FOUND


def test_update_model_file_not_found(test_client, mock_getenv) -> None:
    """
    Test the model file update endpoint for handling a FileNotFoundError.

    Args:
        test_client (TestClient): The test client for making requests.

    Asserts:
        The response status code is 404.
        The response message contains "File Not Found".
    """
    file_name = const.TEST_FILE_NAME
    file_content = io.BytesIO(b"this is a test")
    data = {"model_id": 2, "file_id": 1, "file_description": "model policy file"}
    files = {"files": (file_name, file_content)}

    with patch(
        "app.services.model_register_service.ModelRegisterService.update_model_file"
    ) as mock_upload:
        # Simulate a FileNotFoundError
        mock_upload.side_effect = FileNotFoundError("File Not Found")

        response = test_client.put("/models/file/version", data=data, files=files)

        response_data = response.json()
        expected_substring = "File Not Found"

        # Assert the response JSON 'detail' field contains the expected substring
        assert expected_substring in response_data["detail"]

        # Assert the response status code is 404 (Not Found)
        assert response.status_code == status.HTTP_404_NOT_FOUND


def test_update_model_file_exists_exception(test_client, mock_getenv) -> None:
    """
    Test the model file update endpoint for handling a ModelFileExistsException.

    Args:
        test_client (TestClient): The test client for making requests.

    Asserts:
        The response status code is 409.
        The response message contains "Model File already exists".
    """
    file_name = const.TEST_FILE_NAME
    file_content = io.BytesIO(b"this is a test")
    data = {"model_id": 2, "file_id": 1, "file_description": "model policy file"}
    files = {"files": (file_name, file_content)}

    with patch(
        "app.services.model_register_service.ModelRegisterService.update_model_file"
    ) as mock_upload:
        # Simulate a ModelFileExistsException
        mock_upload.side_effect = ModelFileExistsException("Model File already exists")

        response = test_client.put("/models/file/version", data=data, files=files)

        response_data = response.json()
        expected_substring = "Model File already exists"

        # Assert the response JSON 'detail' field contains the expected substring
        assert expected_substring in response_data["detail"]

        # Assert the response status code is 409 (Conflict)
        assert response.status_code == status.HTTP_409_CONFLICT


def test_fetch_model_file_details(test_client, mock_getenv) -> None:
    """
    Test the model file retrieval endpoint.

    Args:
        test_client (TestClient): The test client for making requests.

    Asserts:
        The response status code is 200.
        The response message is "Model file details retrieved successfully."
        The response data is a list of models.
    """
    data = {"file_name": "Iris", "file_id": 1, "model_id": "1"}

    file_name = const.TEST_FILE_NAME
    with patch(
        "app.services.model_register_service.ModelRegisterService.get_model_file_details"
    ) as mock_upload:
        mock_upload.return_value = {
            "id": 1,
            "model_id": 2,
            "user_id": 2,
            "register_date": "2023-10-01T00:00:00",
            "file_name": file_name,
            "file_path": "s3://bucket_name/path/to/file",
            "file_type": 0,
            "file_description": "model policy file",
        }

        filename = "Iris"
        response = test_client.get(f"/models/file/{filename}/details", params=data)

        response_data = response.json()
        assert response.status_code == status.HTTP_200_OK
        assert response_data["message"] == "Model File Details."
        assert "data" in response_data
        assert response_data["data"]["file_name"] == file_name
        assert response_data["data"]["file_path"] == "s3://bucket_name/path/to/file"
        assert response_data["data"]["model_id"] == 2
        assert response_data["data"]["register_date"] == "2023-10-01T00:00:00"
        assert response_data["data"]["file_type"] == 0
        assert response_data["data"]["id"] == 1


def test_fetch_model_file_details_not_found(test_client, mock_getenv) -> None:
    """
    Test the model file retrieval endpoint.

    Args:
        test_client (TestClient): The test client for making requests.

    Asserts:
        The response status code is 404.
        The response message is "Model File Details."
        The response data is model file details.
    """
    file_name = "Iris"
    data = {"file_name": "Iris", "file_id": 1, "model_id": "1"}
    response = test_client.get(f"/models/file/{file_name}/details", params=data)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    response_data = response.json()
    expected_substring = "Model File Not Found."

    assert expected_substring in response_data["detail"]


def test_delete_model_file_client_error(test_client, mock_getenv) -> None:
    """
    Test the delete model file endpoint for handling a MinIO ClientError.

    Args:
        test_client (TestClient): The test client for making requests.

    Asserts:
        The response status code is 404.
        The response message contains "Minio Client Error:".
    """
    file_id = 1

    with patch(
        "app.services.model_register_service.ModelRegisterService.delete_model_file"
    ) as mock_delete:
        # Simulate a MinIO ClientError
        mock_delete.side_effect = MinioClientError("MinioClient Error")

        response = test_client.delete(f"/models/file/{file_id}")

        response_data = response.json()
        expected_substring = "Minio Client Error:"

        # Assert the response JSON 'detail' field contains the expected substring
        assert expected_substring in response_data["detail"]

        # Assert the response status code is 404 (Not Found)
        assert response.status_code == status.HTTP_404_NOT_FOUND


def test_delete_model_file_model_not_found(
    test_client: TestClient, mock_getenv
) -> None:
    """
    Test the delete model file endpoint for handling a NoResultFound error (Model ID not found).

    Args:
        test_client (TestClient): The test client for making requests.

    Asserts:
        The response status code is 404.
        The response message contains "Model not Found:".
    """
    file_id = 10

    with patch(
        "app.services.model_register_service.ModelRegisterService.delete_model_file"
    ) as mock_delete:
        mock_delete.side_effect = NoResultFound("Model not Found.")

        response = test_client.delete(f"/models/file/{file_id}")

        response_data = response.json()
        expected_substring = "Model not Found."

        # Assert the response JSON 'detail' field contains the expected substring
        assert expected_substring in response_data["detail"]

        # Assert the response status code is 404 (Not Found)
        assert response.status_code == status.HTTP_404_NOT_FOUND


def test_download_model_file_mid_found(test_client: TestClient, mock_getenv) -> None:
    """
    Test the download model file endpoint.

    Args:
        test_client (TestClient): The test client for making requests.

    Asserts:
        The response status code is 200.
        The response content and headers match the mocked response.
    """
    # Create a mock StreamingResponse
    mock_file_content = io.BytesIO(b"mocked zip content")
    mock_response = StreamingResponse(
        mock_file_content,
        media_type="application/x-zip-compressed",
        headers={"Content-Disposition": 'attachment; filename="model-abc.zip"'},
    )

    model_id = 1
    # Patch the `download_model_file` method to return the mock response
    with patch(
        "app.services.model_register_service.ModelRegisterService.download_model_file",
        return_value=mock_response,
    ):
        response = test_client.get(f"/models/file?model_id={model_id}")

        assert response.status_code == status.HTTP_200_OK
        assert response.headers["content-type"] == mock_response.media_type
        assert (
            response.headers["content-disposition"]
            == 'attachment; filename="model-abc.zip"'
        )
        assert response.content == b"mocked zip content"


def test_download_model_file_mid_not_found(test_client: TestClient) -> None:
    """
    Test the download model file endpoint.

    Args:
        test_client (TestClient): The test client for making requests.

    Asserts:
        The response status code is 200.
        The response content and headers match the mocked response.
    """

    # Patch the `download_model_file` method to return the mock response
    model_id = 10
    with patch(
        "app.services.model_register_service.ModelRegisterService.download_model_file",
    ) as mock_response:
        mock_response.side_effect = NoResultFound("Model not Found.")
        response = test_client.get(f"/models/file?{model_id}")

        response_data = response.json()
        expected_substring = "Model not Found:"

        # Assert the response JSON 'detail' field contains the expected substring
        assert expected_substring in response_data["detail"]

        # Assert the response status code is 404 (Not Found)
        assert response.status_code == status.HTTP_404_NOT_FOUND


def test_download_model_file_name_found(test_client: TestClient, mock_getenv) -> None:
    """
    Test the download model file endpoint using model name found.

    Args:
        test_client (TestClient): The test client for making requests.

    Asserts:
        The response status code is 200.
        The response content and headers match the mocked response.
    """
    mock_file_content = io.BytesIO(b"mocked zip content")
    mock_response = StreamingResponse(
        mock_file_content,
        media_type="application/x-zip-compressed",
        headers={"Content-Disposition": 'attachment; filename="model-abc.zip"'},
    )
    model_name = "abc"
    with patch(
        "app.services.model_register_service.ModelRegisterService.download_model_file",
        return_value=mock_response,
    ):
        response = test_client.get(f"/models/file?model_name={model_name}")

        assert response.status_code == status.HTTP_200_OK
        assert response.headers["content-type"] == mock_response.media_type
        assert (
            response.headers["content-disposition"]
            == 'attachment; filename="model-abc.zip"'
        )
        assert response.content == b"mocked zip content"


def test_download_model_file_name_not_found(test_client: TestClient) -> None:
    """
    Test the download model file endpoint using model name not found.

    Args:
        test_client (TestClient): The test client for making requests.

    Asserts:
        The response status code is 404.
        The response content matches the expected error message.
    """
    model_name = "xyz"
    with patch(
        "app.services.model_register_service.ModelRegisterService.download_model_file",
    ) as mock_response:
        mock_response.side_effect = NoResultFound("Model not Found.")
        response = test_client.get(f"/models/file?model_name={model_name}")

        response_data = response.json()
        expected_substring = "Model not Found:"

        assert expected_substring in response_data["detail"]
        assert response.status_code == status.HTTP_404_NOT_FOUND


def test_download_model_file_mid_mname_found(
    test_client: TestClient, mock_getenv
) -> None:
    """
    Test the download model file endpoint using both model ID and model name found.

    Args:
        test_client (TestClient): The test client for making requests.

    Asserts:
        The response status code is 200.
        The response content and headers match the mocked response.
    """
    mock_file_content = io.BytesIO(b"mocked zip content")
    mock_response = StreamingResponse(
        mock_file_content,
        media_type="application/x-zip-compressed",
        headers={"Content-Disposition": 'attachment; filename="model-abc.zip"'},
    )

    model_id = 1
    model_name = "abc"
    with patch(
        "app.services.model_register_service.ModelRegisterService.download_model_file",
        return_value=mock_response,
    ):
        response = test_client.get(
            f"/models/file?model_id={model_id}&model_name={model_name}"
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.headers["content-type"] == mock_response.media_type
        assert (
            response.headers["content-disposition"]
            == 'attachment; filename="model-abc.zip"'
        )
        assert response.content == b"mocked zip content"


def test_download_model_file_mid_mname_not_found(test_client: TestClient) -> None:
    """
    Test the download model file endpoint using both model ID and model name not found.

    Args:
        test_client (TestClient): The test client for making requests.

    Asserts:
        The response status code is 404.
        The response content matches the expected error message.
    """
    model_id = 123
    model_name = "xyz"
    with patch(
        "app.services.model_register_service.ModelRegisterService.download_model_file",
    ) as mock_response:
        mock_response.side_effect = NoResultFound("Model not Found.")
        response = test_client.get(
            f"/models/file?model_id={model_id}&model_name={model_name}"
        )

        response_data = response.json()
        expected_substring = "Model not Found:"

        assert expected_substring in response_data["detail"]
        assert response.status_code == status.HTTP_404_NOT_FOUND


def register_model_uri(test_client: TestClient, mock_getenv):
    """
    Helper function to post the model uri details .

    Args:
       test_client (TestClient): The test client for making requests.

    Asserts:
            The response status code is 201.
            The response content will have model uri details.
    """

    response = test_client.post(
        "/models",
        json={
            "name": "test_model_uri",
            "version": 1,
            "register_user_id": 1,
            "type": "test",
            "description": "A test model",
        },
    )
    result = response.json()
    if response.status_code == status.HTTP_201_CREATED:
        response = test_client.post(
            "/models/uri",
            json={
                "model_id": result["data"]["id"],
                "uri": "s3://mlflow/test.png",
                "description": "A test uri model",
                "file_type": 1,
            },
        )
        return response.json()


def test_register_model_uri(test_client: TestClient, mock_getenv):
    """
    Test the register model uri endpoint .

    Args:
       test_client (TestClient): The test client for making requests.

    Asserts:
            The response status code is 201.
            The response content will have model uri details.
    """

    response = register_model_uri(test_client, mock_getenv)
    assert response["status_code"] == status.HTTP_201_CREATED
    assert response["message"] == "Model uri Registered successfully."
    assert response["data"]["file_description"] == "A test uri model"


def test_register_model_uri_not_found(test_client: TestClient, mock_getenv):
    """
    Test the register model uri endpoint for invalid model_id .

    Args:
       test_client (TestClient): The test client for making requests.

    Asserts:
            The response status code is 404.
            The response content matches the expected error message.
    """

    with patch(
        "app.services.model_register_service.ModelRegisterService.register_model_uri",
    ) as mock_response:
        mock_response.side_effect = NoResultFound("Model Info doesnt exists.")
        response = test_client.post(
            "/models/uri",
            json={
                "model_id": "10",
                "uri": "s3://mlflow/test.png",
                "description": "A test uri model",
                "file_type": 1,
            },
        )

        response_data = response.json()
        expected_substring = "Model Info doesnt exists"

        assert expected_substring in response_data["detail"]
        assert response.status_code == status.HTTP_404_NOT_FOUND


def test_register_model_uri_client_error(test_client: TestClient, mock_getenv) -> None:
    """
    Test the register model uri endpoint for handling a MinIO ClientError.

    Args:
        test_client (TestClient): The test client for making requests.

    Asserts:
        The response status code is 404.
        The response message contains "Minio Client Error".
    """

    with patch(
        "app.services.model_register_service.ModelRegisterService.register_model_uri"
    ) as mock_fetch:
        mock_fetch.side_effect = MinioClientError("MinioClient Error")

        response = test_client.post(
            "/models/uri",
            json={
                "model_id": "10",
                "uri": "s3://mlflow/test.png",
                "description": "A test uri model",
                "file_type": 1,
            },
        )

        response_data = response.json()
        expected_substring = "Minio Client Error:"

        assert expected_substring in response_data["detail"]

        assert response.status_code == status.HTTP_404_NOT_FOUND


def test_fetch_model_uri(test_client: TestClient, mock_getenv):
    """
    Test the fetch model uri endpoint .

    Args:
       test_client (TestClient): The test client for making requests.

    Asserts:
            The response status code is 200.
            The response content will have model uri details.
    """
    uri = "s3://mlflow/test.png"
    response = register_model_uri(test_client, mock_getenv)
    if response == status.HTTP_201_CREATED:
        response = test_client.get(f"/models/uri?{uri}")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["message"] == "Model Uri retrieved successfully."


def test_fetch_model_uri_not_found(test_client: TestClient, mock_getenv):
    """
    Test the fetch model uri endpoint for invalid details .

    Args:
       test_client (TestClient): The test client for making requests.

    Asserts:
            The response status code is 404.
            The response content matches the expected error message.
    """
    uri = "s3://mlflow/test1.png"
    with patch(
        "app.services.model_register_service.ModelRegisterService.fetch_model_uri",
    ) as mock_response:
        mock_response.side_effect = NoResultFound("No Models uri details found.")
        response = test_client.get(f"/models/uri?uri={uri}")

        response_data = response.json()
        expected_substring = "No Models uri details found"

        assert expected_substring in response_data["detail"]
        assert response.status_code == status.HTTP_404_NOT_FOUND


def insert_test_model_data(test_client: TestClient, model_id):
    """
    Helper function to insert test model data into the test database.
    Args:
       test_client (TestClient): The test client for making requests.
    """

    test_client.post(f"/datasets/1/models/{model_id}/link")


def test_save_model_details_success(test_client: TestClient, mock_getenv):
    """
    Test the save model details endpoint for successful case.

    Args:
       test_client (TestClient): The test client for making requests.
       mock_getenv: Mocking environment variables.

    Asserts:
            The response status code is 201.
            The response content matches the expected success message.
    """

    test_file = io.BytesIO(b"test file content")

    with patch(
        "app.services.model_register_service.ModelRegisterService.log_model_in_cogflow"
    ) as mock_response:
        mock_response.return_value = ModelInfo(
            id=1,
            name="test-model",
            version=1,
            description="Test description",
            type="test-type",
            last_modified_time=datetime.utcnow(),
            register_date=datetime.utcnow(),
        )

        response = test_client.post(
            "/models/save",
            files={"files": ("test_model.txt", test_file, "text/plain")},
            data={
                "name": "test-model",
                "file_type": "0",
                "description": "Test description",
            },
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["message"] == "Model Registered in Cogflow Successfully."


def test_save_model_details_model_not_found(test_client: TestClient, mock_getenv):
    """
    Test the save model details endpoint for invalid model_id.

    Args:
       test_client (TestClient): The test client for making requests.
       mock_getenv: Mocking environment variables.

    Asserts:
            The response status code is 404.
            The response content matches the expected error message.
    """

    test_file = io.BytesIO(b"test file content")

    with patch(
        "app.services.model_register_service.ModelRegisterService.log_model_in_cogflow"
    ) as mock_response:
        mock_response.side_effect = NoResultFound("Model not found")

        response = test_client.post(
            "/models/save",
            files={"files": ("test_model.txt", test_file, "text/plain")},
            data={
                "name": "test_model123",
                "file_type": "0",
                "description": "Test description",
            },
        )

        response_data = response.json()
        expected_substring = "Model not Found"

        assert expected_substring in response_data["detail"]
        assert response.status_code == status.HTTP_404_NOT_FOUND


def test_save_model_details_minio_client_error(test_client: TestClient, mock_getenv):
    """
    Test the save model details endpoint for Minio client error.

    Args:
       test_client (TestClient): The test client for making requests.
       mock_getenv: Mocking environment variables.

    Asserts:
            The response status code is 404.
            The response content matches the expected error message.
    """

    test_file = io.BytesIO(b"test file content")

    with patch(
        "app.services.model_register_service.ModelRegisterService.log_model_in_cogflow"
    ) as mock_response:
        mock_response.side_effect = MinioClientError("Minio client error")

        response = test_client.post(
            "/models/save",
            files={"files": ("test_model.txt", test_file, "text/plain")},
            data={
                "name": "test_model",
                "file_type": "0",
                "description": "Test description",
            },
        )

        response_data = response.json()
        expected_substring = "Minio Client Error"

        assert expected_substring in response_data["detail"]
        assert response.status_code == status.HTTP_404_NOT_FOUND


def test_save_model_details_internal_server_error(test_client: TestClient, mock_getenv):
    """
    Test the save model details endpoint for an unexpected error.

    Args:
       test_client (TestClient): The test client for making requests.
       mock_getenv: Mocking environment variables.

    Asserts:
            The response status code is 500.
            The response content matches the expected error message.
    """

    test_file = io.BytesIO(b"test file content")

    with patch(
        "app.services.model_register_service.ModelRegisterService.log_model_in_cogflow"
    ) as mock_response:
        mock_response.side_effect = OperationException("Unexpected error")

        response = test_client.post(
            "/models/save",
            files={"files": ("test_model.txt", test_file, "text/plain")},
            data={
                "name": "test_model",
                "file_type": "0",
                "file_description": "Test description",
            },
        )

        response_data = response.json()
        expected_substring = "Internal Server Error"

        assert expected_substring in response_data["detail"]
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


def test_deploy_model_to_cogflow_success(test_client: TestClient, mock_getenv):
    """
    Test the deploy model endpoint for a successful deployment.

    Args:
       test_client (TestClient): The test client for making requests.
       mock_getenv: Mocking environment variables.

    Asserts:
        The response status code is 201.
        The response content matches the expected success message.
    """

    data = {"name": "Federated Learning", "version": 1, "isvc_name": "fl-svc"}

    with patch(
        "app.services.model_register_service.ModelRegisterService.deploy_model"
    ) as mock_deploy_model:
        mock_deploy_model.return_value = {
            "status": True,
            "msg": "Model Federated Learning deployed with service fl-svc",
        }

        response = test_client.post(
            "/models/service/deploy",
            json=data,
        )
        print("status_code", response)
        response_data = response.json()

        assert response.status_code == status.HTTP_201_CREATED
        assert response_data["message"] == "Model deployed in Cogflow Successfully."


def test_deploy_model_to_cogflow_failure(test_client: TestClient, mock_getenv):
    """
    Test the deploy model endpoint when deployment fails.

    Args:
       test_client (TestClient): The test client for making requests.
       mock_getenv: Mocking environment variables.

    Asserts:
        The response status code is 500.
        The response content matches the expected error message.
    """

    data = {"name": "Federated Learning", "version": 1, "isvc_name": "fl-svc"}

    with patch(
        "app.services.model_register_service.ModelRegisterService.deploy_model"
    ) as mock_deploy_model:
        mock_deploy_model.side_effect = Exception("Internal Server Error:")

        response = test_client.post(
            "/models/service/deploy",
            json=data,
        )

        response_data = response.json()

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Internal Server Error:" in response_data["detail"]


def test_delete_deployed_model_success(test_client: TestClient):
    """
    Test the delete deployed model endpoint for a successful deletion.

    Args:
       test_client (TestClient): The test client for making requests.

    Asserts:
        The response status code is 200.
        The response content matches the expected success message.
    """

    # Mock the response from the delete_deployed_model service method
    with patch(
        "app.services.model_register_service.ModelRegisterService.undeploy_model"
    ) as mock_delete_model:
        mock_delete_model.return_value = (
            "Inference Service fl-svc has been deleted successfully."
        )

        response = test_client.delete(
            "/models/service/undeploy", params={"svc_name": "fl-svc"}
        )

        response_data = response.json()
        print("response_data", response_data)

        # Assertions to validate the response
        assert response.status_code == status.HTTP_200_OK
        assert response_data["message"] == "Inference service Deleted Successfully."
        assert (
            response_data["data"]
            == "Inference Service fl-svc has been deleted successfully."
        )


def test_delete_deployed_model_not_found(test_client: TestClient):
    """
    Test the delete deployed model endpoint for a non-existent service name.

    Args:
       test_client (TestClient): The test client for making requests.

    Asserts:
        The response status code is 404.
        The response content matches the expected error message.
    """

    with patch(
        "app.services.model_register_service.ModelRegisterService.undeploy_model"
    ) as mock_delete_model:
        mock_delete_model.side_effect = Exception("Model not found.")

        response = test_client.delete(
            "/models/service/undeploy", params={"svc_name": "fl-svc"}
        )

        response_data = response.json()

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Internal Server Error" in response_data["detail"]


def test_get_model_associations(test_client):
    """
    Test the get model associations endpoint with model_id.
    Args:
        test_client:

    Returns:

    """
    model_id = 1
    with patch(
        "app.services.model_register_service.ModelRegisterService.fetch_model_with_datasets"
    ) as mock_service:
        mock_service.return_value = [
            {
                "model_id": model_id,
                "model_name": "test_model_name",
                "model_description": None,
                "author": 1,
                "register_date": "2023-10-01T00:00:00",
                "datasets": [],
                "model_files": [],
            }
        ]
        response = test_client.get(f"/models/{model_id}/associations")
        assert response.status_code == 200
        assert response.json() == {
            "status_code": 200,
            "message": "Model Associations",
            "data": [
                {
                    "model_id": model_id,
                    "model_name": "test_model_name",
                    "model_description": None,
                    "author": 1,
                    "register_date": "2023-10-01T00:00:00",
                    "datasets": [],
                    "model_files": [],
                }
            ],
        }


def test_get_model_associations_not_found(test_client):
    """
    Test the get model associations endpoint for a model not found.
    Args:
        test_client:

    Returns:

    """
    model_id = 9999
    with patch(
        "app.services.model_register_service.ModelRegisterService.fetch_model_with_datasets"
    ) as mock_service:
        mock_service.side_effect = NoResultFound("Model not found")
        response = test_client.get(f"/models/{model_id}/associations")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "Model not found" in response.json()["detail"]


def test_get_model_associations_internal_error(test_client: TestClient):
    """
    Test the get model associations endpoint when an unexpected exception is raised.
    Args:
        test_client:

    Returns:

    """
    model_id = 1
    with patch(
        "app.services.model_register_service.ModelRegisterService.fetch_model_with_datasets"
    ) as mock_service:
        mock_service.side_effect = Exception("Unexpected error")
        response = test_client.get(f"/models/{model_id}/associations")
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Internal Server Error" in response.json()["detail"]


def test_get_model_associations_with_datasets(test_client: TestClient):
    """
    Test the get model associations endpoint with a model that has associated datasets.
    Args:
        test_client:

    Returns:

    """
    model_id = 1
    with patch(
        "app.services.model_register_service.ModelRegisterService.fetch_model_with_datasets"
    ) as mock_service:
        mock_service.return_value = [
            {
                "model_id": model_id,
                "model_name": "test_model_name",
                "model_description": "Test model description",
                "author": 1,
                "register_date": "2023-10-01T00:00:00",
                "datasets": [
                    {
                        "id": 1,
                        "dataset_name": "test_dataset",
                        "description": "Test dataset description",
                        "dataset_type": 1,
                        "data_source_type": 2,
                    }
                ],
                "model_files": [],
            }
        ]
        response = test_client.get(f"/models/{model_id}/associations")
        assert response.status_code == 200
        assert response.json() == {
            "status_code": 200,
            "message": "Model Associations",
            "data": [
                {
                    "model_id": model_id,
                    "model_name": "test_model_name",
                    "model_description": "Test model description",
                    "author": 1,
                    "register_date": "2023-10-01T00:00:00",
                    "datasets": [
                        {
                            "id": 1,
                            "dataset_name": "test_dataset",
                            "description": "Test dataset description",
                            "dataset_type": 1,
                            "data_source_type": 2,
                        }
                    ],
                    "model_files": [],
                }
            ],
        }


def test_get_model_associations_with_files(test_client):
    """
    Test the get model associations endpoint with a model that has associated files.
    Args:
        test_client:

    Returns:

    """
    model_id = 1
    with patch(
        "app.services.model_register_service.ModelRegisterService.fetch_model_with_datasets"
    ) as mock_service:
        mock_service.return_value = [
            {
                "model_id": model_id,
                "model_name": "test_model_name",
                "model_description": "Test model description",
                "author": 1,
                "register_date": "2023-10-01T00:00:00",
                "datasets": [],
                "model_files": [{"file_id": 1, "file_name": "test_file.txt"}],
            }
        ]
        response = test_client.get(f"/models/{model_id}/associations")
        assert response.status_code == 200
        assert response.json() == {
            "status_code": 200,
            "message": "Model Associations",
            "data": [
                {
                    "model_id": model_id,
                    "model_name": "test_model_name",
                    "model_description": "Test model description",
                    "author": 1,
                    "register_date": "2023-10-01T00:00:00",
                    "datasets": [],
                    "model_files": [{"file_id": 1, "file_name": "test_file.txt"}],
                }
            ],
        }


def test_get_model_associations_with_datasets_and_files(test_client):
    """
    Test the get model associations endpoint with a model that has both associated datasets and files.
    Args:
        test_client:

    Returns:

    """
    model_id = 1
    with patch(
        "app.services.model_register_service.ModelRegisterService.fetch_model_with_datasets"
    ) as mock_service:
        mock_service.return_value = [
            {
                "model_id": model_id,
                "model_name": "test_model_name",
                "model_description": "Test model description",
                "author": 1,
                "register_date": "2023-10-01T00:00:00",
                "datasets": [
                    {
                        "id": 1,
                        "dataset_name": "test_dataset",
                        "description": "Test dataset description",
                        "dataset_type": 1,
                        "data_source_type": 1,
                    }
                ],
                "model_files": [{"file_id": 1, "file_name": "test_file.txt"}],
            }
        ]
        response = test_client.get(f"/models/{model_id}/associations")
        assert response.status_code == 200
        assert response.json() == {
            "status_code": 200,
            "message": "Model Associations",
            "data": [
                {
                    "model_id": model_id,
                    "model_name": "test_model_name",
                    "model_description": "Test model description",
                    "author": 1,
                    "register_date": "2023-10-01T00:00:00",
                    "datasets": [
                        {
                            "id": 1,
                            "dataset_name": "test_dataset",
                            "description": "Test dataset description",
                            "dataset_type": 1,
                            "data_source_type": 1,
                        }
                    ],
                    "model_files": [{"file_id": 1, "file_name": "test_file.txt"}],
                }
            ],
        }


def test_get_model_associations_invalid_id(test_client):
    """
    Test the get model associations endpoint with an invalid ID parameter.
    Args:
        test_client:

    Returns:

    """
    # Test with a non-integer ID
    response = test_client.get("/models/invalid/associations")
    assert response.status_code == 422

    # Test with a negative ID
    response = test_client.get("/models/-1/associations")
    assert response.status_code == 422


def test_get_model_associations_by_name(test_client):
    """
    Test the get model associations by name endpoint with a valid name.
    Args:
        test_client: The test client fixture

    Returns:
        None
    """
    model_name = "test_model"
    with patch(
        "app.services.model_register_service.ModelRegisterService.fetch_model_with_datasets_by_name"
    ) as mock_service:
        mock_service.return_value = [
            {
                "model_id": 1,
                "model_name": "test_model_name",
                "model_description": None,
                "author": 1,
                "register_date": "2023-10-01T00:00:00",
                "datasets": [],
                "model_files": [],
            }
        ]
        response = test_client.get(f"/models/associations?name={model_name}")
        assert response.status_code == 200
        assert response.json() == {
            "status_code": 200,
            "message": "Model Associations by Name",
            "data": [
                {
                    "model_id": 1,
                    "model_name": "test_model_name",
                    "model_description": None,
                    "author": 1,
                    "register_date": "2023-10-01T00:00:00",
                    "datasets": [],
                    "model_files": [],
                }
            ],
        }


def test_get_model_associations_by_name_not_found(test_client):
    """
    Test the get model associations by name endpoint for a model not found.
    Args:
        test_client: The test client fixture

    Returns:
        None
    """
    model_name = "nonexistent_model"
    with patch(
        "app.services.model_register_service.ModelRegisterService.fetch_model_with_datasets_by_name"
    ) as mock_service:
        mock_service.side_effect = NoResultFound("No Result found for the given name")
        response = test_client.get(f"/models/associations?name={model_name}")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "No Result found for the given name" in response.json()["detail"]


def test_get_model_associations_by_name_internal_error(test_client):
    """
    Test the get model associations by name endpoint when an unexpected exception is raised.
    Args:
        test_client: The test client fixture

    Returns:
        None
    """
    model_name = "test_model"
    with patch(
        "app.services.model_register_service.ModelRegisterService.fetch_model_with_datasets_by_name"
    ) as mock_service:
        mock_service.side_effect = Exception("Unexpected error")
        response = test_client.get(f"/models/associations?name={model_name}")
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Internal Server Error" in response.json()["detail"]


def test_get_model_associations_by_name_with_datasets(test_client):
    """
    Test the get model associations by name endpoint with a model that has associated datasets.
    Args:
        test_client: The test client fixture

    Returns:
        None
    """
    model_name = "test_model"
    with patch(
        "app.services.model_register_service.ModelRegisterService.fetch_model_with_datasets_by_name"
    ) as mock_service:
        mock_service.return_value = [
            {
                "model_id": 1,
                "model_name": "test_model_name",
                "model_description": "Test model description",
                "author": 1,
                "register_date": "2023-10-01T00:00:00",
                "datasets": [
                    {
                        "id": 1,
                        "dataset_name": "test_dataset",
                        "description": "Test dataset description",
                        "dataset_type": 1,
                        "data_source_type": 2,
                    }
                ],
                "model_files": [],
            }
        ]
        response = test_client.get(f"/models/associations?name={model_name}")
        assert response.status_code == 200
        assert response.json() == {
            "status_code": 200,
            "message": "Model Associations by Name",
            "data": [
                {
                    "model_id": 1,
                    "model_name": "test_model_name",
                    "model_description": "Test model description",
                    "author": 1,
                    "register_date": "2023-10-01T00:00:00",
                    "datasets": [
                        {
                            "id": 1,
                            "dataset_name": "test_dataset",
                            "description": "Test dataset description",
                            "dataset_type": 1,
                            "data_source_type": 2,
                        }
                    ],
                    "model_files": [],
                }
            ],
        }


def test_get_model_associations_by_name_with_files(test_client):
    """
    Test the get model associations by name endpoint with a model that has associated files.
    Args:
        test_client: The test client fixture

    Returns:
        None
    """
    model_name = "test_model"
    with patch(
        "app.services.model_register_service.ModelRegisterService.fetch_model_with_datasets_by_name"
    ) as mock_service:
        mock_service.return_value = [
            {
                "model_id": 1,
                "model_name": "test_model_name",
                "model_description": "Test model description",
                "author": 1,
                "register_date": "2023-10-01T00:00:00",
                "datasets": [],
                "model_files": [{"file_id": 1, "file_name": "test_file.txt"}],
            }
        ]
        response = test_client.get(f"/models/associations?name={model_name}")
        assert response.status_code == 200
        assert response.json() == {
            "status_code": 200,
            "message": "Model Associations by Name",
            "data": [
                {
                    "model_id": 1,
                    "model_name": "test_model_name",
                    "model_description": "Test model description",
                    "author": 1,
                    "register_date": "2023-10-01T00:00:00",
                    "datasets": [],
                    "model_files": [{"file_id": 1, "file_name": "test_file.txt"}],
                }
            ],
        }


def test_get_model_associations_by_name_with_datasets_and_files(test_client):
    """
    Test the get model associations by name endpoint with a model that has both associated datasets and files.
    Args:
        test_client: The test client fixture

    Returns:
        None
    """
    model_name = "test_model"
    with patch(
        "app.services.model_register_service.ModelRegisterService.fetch_model_with_datasets_by_name"
    ) as mock_service:
        mock_service.return_value = [
            {
                "model_id": 1,
                "model_name": "test_model_name",
                "model_description": "Test model description",
                "author": 1,
                "register_date": "2023-10-01T00:00:00",
                "datasets": [
                    {
                        "id": 1,
                        "dataset_name": "test_dataset",
                        "description": "Test dataset description",
                        "dataset_type": 1,
                        "data_source_type": 2,
                    }
                ],
                "model_files": [{"file_id": 1, "file_name": "test_file.txt"}],
            }
        ]
        response = test_client.get(f"/models/associations?name={model_name}")
        assert response.status_code == 200
        assert response.json() == {
            "status_code": 200,
            "message": "Model Associations by Name",
            "data": [
                {
                    "model_id": 1,
                    "model_name": "test_model_name",
                    "model_description": "Test model description",
                    "author": 1,
                    "register_date": "2023-10-01T00:00:00",
                    "datasets": [
                        {
                            "id": 1,
                            "dataset_name": "test_dataset",
                            "description": "Test dataset description",
                            "dataset_type": 1,
                            "data_source_type": 2,
                        }
                    ],
                    "model_files": [{"file_id": 1, "file_name": "test_file.txt"}],
                }
            ],
        }


def test_get_model_associations_by_name_multiple_models(test_client):
    """
    Test the get model associations by name endpoint when multiple models match the name.
    Args:
        test_client: The test client fixture

    Returns:
        None
    """
    model_name = "test"
    with patch(
        "app.services.model_register_service.ModelRegisterService.fetch_model_with_datasets_by_name"
    ) as mock_service:
        mock_service.return_value = [
            {
                "model_id": 1,
                "model_name": "test_model_1",
                "model_description": "Test model 1",
                "author": 1,
                "register_date": "2023-10-01T00:00:00",
                "datasets": [],
                "model_files": [],
            },
            {
                "model_id": 2,
                "model_name": "test_model_2",
                "model_description": "Test model 2",
                "author": 1,
                "register_date": "2023-10-02T00:00:00",
                "datasets": [],
                "model_files": [],
            },
        ]
        response = test_client.get(f"/models/associations?name={model_name}")
        assert response.status_code == 200
        assert response.json() == {
            "status_code": 200,
            "message": "Model Associations by Name",
            "data": [
                {
                    "model_id": 1,
                    "model_name": "test_model_1",
                    "model_description": "Test model 1",
                    "author": 1,
                    "register_date": "2023-10-01T00:00:00",
                    "datasets": [],
                    "model_files": [],
                },
                {
                    "model_id": 2,
                    "model_name": "test_model_2",
                    "model_description": "Test model 2",
                    "author": 1,
                    "register_date": "2023-10-02T00:00:00",
                    "datasets": [],
                    "model_files": [],
                },
            ],
        }
