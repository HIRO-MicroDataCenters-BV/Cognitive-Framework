"""
Test cases for the datasets endpoints.
"""

import io
import random
import uuid
from typing import Dict
from unittest.mock import patch

from fastapi import status

from app.utils.exceptions import NoResultFound
from config import constants as const


def test_register_dataset(test_client) -> None:
    """
    Test the registration of a dataset.

    Args:
        test_client: The test client to use for making the request.

    Asserts:
        The response status code is 201.
        The response contains the expected dataset details.
    """
    file_name = "testfile.csv"
    file_content = io.BytesIO(b"file content")
    data = {
        "dataset_type": 1,
        "user_id": 1,
        "name": "Test Dataset",
        "description": "Test Description",
    }
    files = {"files": (file_name, file_content)}

    def mock_getenv(key, default=None):
        env_vars = {
            "MLFLOW_S3_ENDPOINT_URL": "localhost:9000",
            "AWS_ACCESS_KEY_ID": "minio",
            "AWS_SECRET_ACCESS_KEY": "minio123",
            "CONFIG_TYPE": "config.app_config.DevelopmentConfig",
        }
        return env_vars.get(key, default)

    with patch("os.getenv", side_effect=mock_getenv):
        with patch(
            "app.services.dataset_service.DatasetService.upload_file"
        ) as mock_upload:
            mock_upload.return_value = {
                "id": 1,
                "dataset_type": 1,
                "user_id": 1,
                "register_date": "2023-10-01T00:00:00",
                "file_name": file_name,
                "file_path": "s3://bucket_name/path/to/file",
                "file_description": "Test Description",
            }

            response = test_client.post("/datasets/file", data=data, files=files)
            response_data = response.json()
            assert response.status_code == status.HTTP_201_CREATED
            assert response_data["message"] == "File uploaded successfully."
            assert "data" in response_data
            assert response_data["data"]["file_name"] == "testfile.csv"
            assert response_data["data"]["file_path"] == "s3://bucket_name/path/to/file"
            assert response_data["data"]["dataset_type"] == 1
            assert response_data["data"]["user_id"] == 1
            assert response_data["data"]["register_date"] == "2023-10-01T00:00:00"
            assert response_data["data"]["file_description"] == "Test Description"
            assert response_data["data"]["id"] == 1


def test_update_dataset_invalid_dataset_type(test_client) -> None:
    """
    Test validation error for invalid dataset_type during dataset update.

    Args:
        test_client: The test client to use for making the request.

    Asserts:
        The response status code is 422 for invalid dataset_type.
        The response contains the correct validation error message.
    """
    file_name = "testfile.csv"
    file_content = io.BytesIO(b"invalid file content")
    data = {
        "id": 1,
        "dataset_type": 3,  # Invalid dataset_type (valid: 0, 1, 2)
        "name": "dataset_update",
        "description": "Invalid Description",
    }
    files = {"files": (file_name, file_content)}

    response = test_client.put("/datasets/file", data=data, files=files)
    response_data = response.json()

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert "detail" in response_data
    assert const.DATASET_TYPE_ERROR_MESSAGE in response_data["detail"]


def test_update_dataset(test_client, mock_getenv) -> None:
    """
    Test the update of a dataset.

    Args:
        test_client: The test client to use for making the request.

    Asserts:
        The response status code is 200.
        The response contains the expected dataset details.
    """
    file_name = "testfile.csv"
    file_content = io.BytesIO(b"file content")
    data = {
        "dataset_type": 1,
        "user_id": 1,
        "name": "Test Dataset",
        "description": "Test Description",
        "id": 1,
    }
    files = {"files": (file_name, file_content)}
    with patch(
        "app.services.dataset_service.DatasetService.update_file"
    ) as mock_update:
        mock_update.return_value = {
            "id": 1,
            "dataset_type": 1,
            "user_id": 1,
            "register_date": "2023-10-01T00:00:00",
            "file_name": file_name,
            "file_path": "s3://bucket_name/path/to/file",
            "file_description": "Test Description",
        }

        response = test_client.put("/datasets/file", data=data, files=files)
        response_data = response.json()
        assert response.status_code == status.HTTP_200_OK
        assert response_data["message"] == "File updated successfully."
        assert "data" in response_data
        assert response_data["data"]["file_name"] == "testfile.csv"
        assert response_data["data"]["file_path"] == "s3://bucket_name/path/to/file"
        assert response_data["data"]["dataset_type"] == 1
        assert response_data["data"]["user_id"] == 1
        assert response_data["data"]["register_date"] == "2023-10-01T00:00:00"
        assert response_data["data"]["file_description"] == "Test Description"
        assert response_data["data"]["id"] == 1


def test_fetch_datasets(test_client):
    """
    Test fetching all datasets.

    Args:
        test_client: The test client to use for making the request.

    Asserts:
        The response status code is 200.
        The response contains the expected datasets.
    """
    file_name = "testfile.csv"
    file_content = io.BytesIO(b"file content")
    data = {
        "dataset_type": 1,
        "user_id": 1,
        "name": "Test Dataset",
        "description": "Test Description",
    }
    files = {"files": (file_name, file_content)}

    def mock_getenv(key, default=None):
        env_vars = {
            "MLFLOW_S3_ENDPOINT_URL": "localhost:9000",
            "AWS_ACCESS_KEY_ID": "minio",
            "AWS_SECRET_ACCESS_KEY": "minio123",
            "CONFIG_TYPE": "config.app_config.DevelopmentConfig",
        }
        return env_vars.get(key, default)

    with patch("os.getenv", side_effect=mock_getenv):
        with patch(
            "app.services.dataset_service.DatasetService.upload_file"
        ) as mock_upload:
            mock_upload.return_value = {
                "id": 1,
                "dataset_type": 1,
                "user_id": 1,
                "register_date": "2023-10-01T00:00:00",
                "file_name": file_name,
                "file_path": "s3://bucket_name/path/to/file",
                "file_description": "Test Description",
            }

            response = test_client.post("/datasets/file", data=data, files=files)
            assert response.status_code == status.HTTP_201_CREATED

    mock_datasets = [
        {
            "id": 1,
            "dataset_type": 1,
            "user_id": 1,
            "register_date": "2023-10-01T00:00:00",
            "file_name": "testfile.csv",
            "file_path": "s3://bucket_name/path/to/file",
            "file_description": "Test Description",
        }
    ]

    with patch(
        "app.services.dataset_service.DatasetService.search_datasets"
    ) as mock_search:
        mock_search.return_value = mock_datasets

        response = test_client.get("/datasets")
        print(f"DEBUG: Get response: {response.json()}")  # Debug statement
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["message"] == "All datasets"
        assert len(response.json()["data"]) > 0


def test_fetch_datasets_with_filters(test_client):
    """
    Test fetching datasets with filters.

    Args:
        test_client: The test client to use for making the request.

    Asserts:
        The response status code is 200.
        The response contains the filtered datasets.
    """
    mock_datasets = [
        {
            "id": 1,
            "dataset_type": 1,
            "user_id": 1,
            "register_date": "2023-10-01T00:00:00",
            "file_name": "testfile.csv",
            "file_path": "s3://bucket_name/path/to/file",
            "file_description": "Test Description",
        }
    ]

    with patch(
        "app.services.dataset_service.DatasetService.search_datasets"
    ) as mock_search:
        mock_search.return_value = mock_datasets

        response = test_client.get("/datasets", params={"name": "Test Dataset"})
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["message"] == "Filtered dataset details"


def test_delete_dataset(test_client):
    """
    Test deleting a dataset.

    Args:
        test_client: The test client to use for making the request.

    Asserts:
        The response status code is 200.
        The response contains the expected deletion message.
    """
    with patch(
        "app.services.dataset_service.DatasetService.deregister_dataset"
    ) as mock_delete:
        mock_delete.return_value = {"message": "Dataset deleted successfully"}

        response = test_client.delete("/datasets/file/1")
        assert response.status_code == status.HTTP_204_NO_CONTENT


def test_link_dataset_model(test_client):
    """
    Test linking a dataset to a model.

    Args:
        test_client: The test client to use for making the request.

    Asserts:
        The response status code is 201.
        The response contains the expected linking message.
    """
    with patch(
        "app.services.dataset_service.DatasetService.link_dataset_model"
    ) as mock_link:
        mock_link.return_value = {"message": "Dataset linked with model successfully"}

        response = test_client.post("/datasets/1/models/1/link")
        print(f"DEBUG: Post response status: {response.status_code}")
        print(f"DEBUG: Post response JSON: {response.json()}")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["message"] == "Dataset linked with model successfully"


def test_unlink_dataset_model(test_client):
    """
    Test unlinking a dataset from a model.

    Args:
        test_client: The test client to use for making the request.

    Asserts:
        The response status code is 200.
        The response contains the expected unlinking message.
    """
    with patch(
        "app.services.dataset_service.DatasetService.unlink_dataset_model"
    ) as mock_unlink:
        mock_unlink.return_value = {
            "message": "Dataset unlinked from model successfully"
        }

        response = test_client.post("/datasets/1/models/1/unlink")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["message"] == "Dataset unlinked from model successfully"


def test_link_dataset_model_not_found(test_client):
    """
    Test linking a dataset to a model when the dataset or model is not found.

    Args:
        test_client: The test client to use for making the request.

    Asserts:
        The response status code is 404.
        The response contains the expected error message.
    """
    with patch(
        "app.services.dataset_service.DatasetService.link_dataset_model"
    ) as mock_link:
        mock_link.side_effect = NoResultFound("Dataset or model not found.")

        response = test_client.post("/datasets/999/models/999/link")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()["detail"] == "Dataset or model not found."


def test_unlink_dataset_model_not_found(test_client):
    """
    Test unlinking a dataset from a model when the dataset or model is not found.

    Args:
        test_client: The test client to use for making the request.

    Asserts:
        The response status code is 404.
        The response contains the expected error message.
    """
    with patch(
        "app.services.dataset_service.DatasetService.unlink_dataset_model"
    ) as mock_unlink:
        mock_unlink.side_effect = NoResultFound("Dataset or model not found.")

        response = test_client.post("/datasets/999/models/999/unlink")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()["detail"] == "Dataset or model not found."


def test_fetch_tables(test_client):
    """
    Test fetch tables for any given url.

    Args:
        test_client: The test client to use for making the request.

    Asserts:
        The response status code is 200.
        The response contains the database table info.
    """
    mock_datasets = [
        {
            "cognitivedb": [
                {
                    "table_name": "dataset_table_registrater",
                    "fields": "id: INTEGER(), dataset_id: INTEGER(),"
                    "user_id: INTEGER(), register_date: TIMESTAMP(),"
                    "db_url: VARCHAR(), table_name: VARCHAR(), "
                    "fields_selected_list: VARCHAR()",
                    "records_count": 2,
                }
            ]
        }
    ]

    with patch(
        "app.services.dataset_service.DatasetService.fetch_db_tables"
    ) as mock_search:
        mock_search.return_value = mock_datasets

        response = test_client.get(
            "/datasets/tables",
            params={"url": "postgresql://hiro:test@postgres:5432/testdb"},
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["message"] == "Tables Details."


def test_fetch_tables_not_found(test_client):
    """
    Test fetch tables for any invalid url.

    Args:
        test_client: The test client to use for making the request.

    Asserts:
        The response status code is 503.
        The response will throw DatabaseError.
    """

    response = test_client.get(
        "/datasets/tables",
        params={"url": "postgresql1://hiro:hiropwd@localhost:5433/cognitivedb"},
    )
    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    assert "Database Exception in while fetching details" in response.json()["detail"]


def test_dataset_table_register(test_client):
    """
    Test dataset tables registration.
    Args:
      test_client: The test client to use for making the request.

    Asserts:
        The response status code is 201.
        The response will contain DatasetTable details.
    """
    data = {
        "dataset_type": 2,
        "name": "1.0",
        "description": "dataset table registration",
        "table_name": "model_test",
        "selected_fields": "version1,id",
        "db_url": "postgresql1://hiro:hiropwd@localhost:5433/cognitivedb",
    }
    response = test_client.post("/datasets/table", json=data)
    assert response.json()["status_code"] == status.HTTP_201_CREATED
    assert response.json()["message"] == "Dataset table Register Details"


def test_dataset_table_register_exists(test_client):
    """
    Test dataset tables registration.
    Args:
      test_client: The test client to use for making the request.

    Asserts:
        The response status code is 409.
        The response will throw IntegrityError.
    """
    data = {
        "dataset_type": 1,
        "name": "1.0",
        "description": "dataset table registration",
        "table_name": "model_info",
        "selected_fields": "version,id",
        "db_url": "postgresql1://hiro:hiropwd@localhost:5433/cognitivedb",
    }
    test_client.post("/datasets/table", json=data)
    response1 = test_client.post("/datasets/table", json=data)

    assert "Dataset table Already Exists." in response1.json()["detail"]["message"]
    assert response1.status_code == status.HTTP_409_CONFLICT


def test_dataset_table_register_update(test_client):
    """
    Test dataset tables register update.
    Args:
      test_client: The test client to use for making the request.

    Asserts:
        The response status code is 200.
        The response will contain DatasetTable details.
    """
    data1 = {
        "dataset_type": 1,
        "name": "1.0",
        "description": "dataset table registration",
        "table_name": "model_info",
        "selected_fields": "version,id",
        "db_url": "postgresql1://hiro:hiropwd@localhost:5433/cognitivedb",
    }
    test_client.post("/datasets/table", json=data1)

    update_data = {
        "dataset_type": 1,
        "name": "1.0",
        "description": "dataset table register",
        "table_name": "model_info",
        "selected_fields": "version,id1",
        "db_url": "postgresql1://hiro:hiropwd@localhost:5433/cognitivedb",
    }
    response = test_client.put("/datasets/table", json=update_data)

    assert response.json()["status_code"] == status.HTTP_200_OK
    assert response.json()["message"] == "Dataset table Register Details Updated"


def test_dataset_table_register_update_exists(test_client):
    """
    Test dataset tables register update.
    Args:
      test_client: The test client to use for making the request.

    Asserts:
        The response status code is 409.
        The response will throw IntegrityError.
    """
    post_data = {
        "dataset_type": 1,
        "name": "2.0",
        "description": "dataset table registration",
        "table_name": "model_table",
        "selected_fields": "version,id",
        "db_url": "postgresql1://hiro:hiropwd@localhost:5433/cognitivedb",
    }
    test_client.post("/datasets/table", json=post_data)
    update_data = {
        "dataset_type": 1,
        "name": "2.0",
        "description": "dataset table registration",
        "table_name": "model_table",
        "selected_fields": "version,id",
        "db_url": "postgresql1://hiro:hiropwd@localhost:5433/cognitivedb",
    }
    response = test_client.put("/datasets/table", json=update_data)

    assert "Dataset Table Register Details Already Exists" in response.json()["detail"]
    assert response.status_code == status.HTTP_409_CONFLICT


def test_dataset_table_register_update_not_found(test_client):
    """
    Test dataset tables register update for incorrect data.
    Args:
      test_client: The test client to use for making the request.

    Asserts:
        The response status code is 404.
        The response will throw NoResultFound.
    """
    data = {
        "dataset_type": 1,
        "name": "10.0",
        "description": "dataset table registration",
        "table_name": "model_info1",
        "selected_fields": "version,id",
        "db_url": "postgresql1://hiro:hiropwd@localhost:5433/cognitivedb",
    }
    response = test_client.put("/datasets/table", json=data)

    assert "Dataset Not Registered. Error:" in response.json()["detail"]
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_fetch_file_datasets_details(test_client, mock_getenv):
    """
    Test the dataset file details retrieval endpoint with a valid dataset ID.

    Args:
        test_client (TestClient): The test client for making requests.

    Asserts:
        The response status code is 200.
        The response message is "Dataset File Details."
        The response data contains details about the dataset files.
    """
    dataset_id = 1
    data = {
        "file_id": 1,
        "file_name": "dataset_file_1.csv",
        "file_path": "s3://bucket_name/path/to/file",
        "register_date": "2023-10-01T00:00:00",
    }

    with patch(
        "app.services.dataset_service.DatasetService.fetch_file_details_for_dataset"
    ) as mock_service:
        mock_service.return_value = [data]

        response = test_client.get(f"/datasets/{dataset_id}/file")

        response_data = response.json()
        assert response.status_code == status.HTTP_200_OK
        assert response_data["message"] == "Dataset File Details"
        assert "data" in response_data
        assert response_data["data"][0]["file_name"] == "dataset_file_1.csv"
        assert response_data["data"][0]["file_path"] == "s3://bucket_name/path/to/file"
        assert response_data["data"][0]["register_date"] == "2023-10-01T00:00:00"


def test_fetch_file_datasets_details_not_found(test_client, mock_getenv):
    """
    Test the dataset file details retrieval endpoint with a nonexistent dataset ID.

    Args:
        test_client (TestClient): The test client for making requests.

    Asserts:
        The response status code is 404.
        The response detail is "Dataset not found."
    """
    dataset_id = 123
    with patch(
        "app.services.dataset_service.DatasetService.fetch_file_details_for_dataset"
    ) as mock_service:
        mock_service.side_effect = NoResultFound

        response = test_client.get(f"/datasets/{dataset_id}/file")

        response_data = response.json()
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response_data["detail"] == "Dataset not found."


def test_fetch_file_datasets_details_invalid_dataset_id(test_client):
    """
    Test the dataset file details retrieval endpoint with an invalid dataset ID.

    Args:
        test_client (TestClient): The test client for making requests.

    Asserts:
        The response status code is 422.
        The response detail contains a validation error.
    """
    dataset_id = -1
    response = test_client.get(f"/datasets/{dataset_id}/file")

    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert response_data["detail"][0]["msg"] == "ensure this value is greater than 0"


def test_fetch_dataset_table(test_client):
    """
    Test dataset table details
    Args:
      test_client: The test client to use for making the request.

    Asserts:
        The response status code is 200.
    """
    post_data = {
        "dataset_type": 1,
        "name": "2.0",
        "description": "dataset table registration",
        "table_name": "model_test_register",
        "selected_fields": "version,id",
        "db_url": "postgresql1://hiro:hiropwd@localhost:5433/cognitivedb",
    }
    response = test_client.post("/datasets/table", json=post_data)
    response_data = response.json()
    dataset_id = response_data["data"]["dataset_id"]
    response = test_client.get(f"/datasets/{dataset_id}/table")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["message"] == "Dataset Table Details"


def test_fetch_dataset_table_not_found(test_client):
    """
    Test dataset table details for not found value
    Args:
      test_client: The test client to use for making the request.

    Asserts:
        The response status code is 404.
    """
    dataset_id = 10
    response = test_client.get(f"/datasets/{dataset_id}/table")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Dataset not found."


def test_fetch_dataset_table_exception(test_client):
    """
    Test dataset table details for not Exception
    Args:
      test_client: The test client to use for making the request.

    Asserts:
        The response status code is 500.
    """
    dataset_id = 10
    with patch(
        "app.services.dataset_service.DatasetService.fetch_table_details_for_dataset"
    ) as mock_search:
        mock_search.side_effect = Exception()

        response = test_client.get(f"/datasets/{dataset_id}/table")
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.json()["detail"] in "Internal Exception:"


def test_fetch_dataset_table_invalid_dataset(test_client):
    """
    Test dataset table details for invalid dataset
    Args:
      test_client: The test client to use for making the request.

    Asserts:
        The response status code is 422.
    """
    dataset_id = -10
    response = test_client.get(f"/datasets/{dataset_id}/table")
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    response_msg = response.json()
    assert response_msg["detail"][0]["msg"] == "ensure this value is greater than 0"


def broker_data() -> Dict[str, str]:
    """
    data for broker registration
    Returns:

    """
    data = {
        "name": f"broker-{uuid.uuid4().hex[:6]}",
        "ip": f"{random.randint(1, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}."
        f"{random.randint(0, 255)}",
        "port": "9092",
    }
    return data


def test_fetch_broker_details_not_found(test_client):
    """
    Test for fetching broker details for broker not found.

    Args:
        test_client: The test client to use for making the request.

    Returns:
        The response status code is 404.
    """

    response = test_client.get("/datasets/broker/details")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "No Broker defined."


def test_fetch_topic_details_not_found(test_client):
    """
    Test for fetching topic details for broker not found.

    Args:
        test_client: The test client to use for making the request.

    Returns:
        The response status code is 404.
    """

    response = test_client.get("/datasets/topic/details")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "No Topic defined."


def test_dataset_broker_register(test_client):
    """
     Test successful broker registration
    Args:
        test_client: The test client to use for making the request.

    Returns:
         The response status code is 201.
    """
    data = broker_data()
    response = test_client.post("/datasets/broker", json=data)
    assert response.json()["status_code"] == status.HTTP_201_CREATED
    assert response.json()["message"] == "Broker created successfully."


def test_dataset_broker_register_integrity_error(test_client):
    """
      Test for broker registration integrity error
    Args:
        test_client: The test client to use for making the request.

    Returns:
         The response status code is 409.
    """
    data = {"name": "broker1", "ip": "127.0.0.1", "port": "9092"}
    test_client.post("/datasets/broker", json=data)
    response = test_client.post("/datasets/broker", json=data)
    assert response.status_code == status.HTTP_409_CONFLICT
    assert "Broker id" in response.json()["detail"]["message"]


def test_dataset_broker_register_invalid_ip(test_client):
    """
      Test for broker registration exception
    Args:
        test_client: The test client to use for making the request.

    Returns:
        The response status code is 409.
    """
    data = {"name": "broker2", "ip": "test", "port": "9092"}
    test_client.post("/datasets/broker", json=data)
    response = test_client.post("/datasets/broker", json=data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert (
        response.json()["detail"][0]["msg"]
        == "value is not a valid IPv4 or IPv6 address"
    )


def test_dataset_topic_register(test_client):
    """
    Test successful topic registration.

    Args:
        test_client: The test client to use for making the request.

    Returns:
        The response status code is 201.
    """
    broker_response = test_client.post("/datasets/broker", json=broker_data())
    data = {
        "name": f"topic-{uuid.uuid4().hex[:6]}",
        "schema": {"key1": "value1", "key2": "value2"},
        "broker_id": broker_response.json()["data"]["id"],
    }
    if broker_response.status_code == 201:
        response = test_client.post(
            f"/datasets/broker/{data['broker_id']}/topic", json=data
        )
        assert response.json()["status_code"] == status.HTTP_201_CREATED
        assert response.json()["message"] == "Topic created successfully"


def test_dataset_topic_register_integrity_error(test_client):
    """
    Test for topic registration integrity error (topic already exists).

    Args:
        test_client: The test client to use for making the request.

    Returns:
        The response status code is 409.
    """
    broker_response = test_client.post("/datasets/broker/register", json=broker_data())
    if broker_response.status_code == 201:
        data = {
            "name": "topic1",
            "schema": {"field1": "string", "field2": "integer"},
            "broker_id": broker_response.json()["data"]["id"],
        }
        test_client.post("/datasets/topic/register", json=data)
        response = test_client.post("/datasets/topic/register", json=data)
        assert response.status_code == status.HTTP_409_CONFLICT
        assert "Topic Integrity Error:" in response.json()["detail"]["message"]


def test_dataset_topic_register_foreign_key_error(test_client):
    """
    Test for topic registration integrity error (foreign key violation).

    Args:
        test_client: The test client to use for making the request.

    Returns:
        The response status code is 409.
    """
    broker_id = 111
    data = {
        "name": "topic2",
        "schema": {"field1": "string", "field2": "integer"},
        "broker_id": broker_id,  # Assuming broker ID does not exist
    }
    response = test_client.post(
        f"/datasets/broker/{data['broker_id']}/topic", json=data
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert f"Broker Id {broker_id} not found." in response.json()["detail"]


def test_fetch_broker_details(test_client):
    """
    Test for fetching broker details.

    Args:
        test_client: The test client to use for making the request.

    Returns:
        The response status code is 200.
    """
    data = broker_data()
    response = test_client.post("/datasets/broker", json=data)
    if response.status_code == status.HTTP_200_OK:
        response = test_client.get("/dataset/broker/details")
        assert response.json()["status_code"] == status.HTTP_200_OK
        assert response.json()["message"] == "Broker Details"


def test_fetch_topic_details(test_client):
    """
    Test for fetching topic details.

    Args:
        test_client: The test client to use for making the request.

    Returns:
        The response status code is 200.
    """
    broker_response = test_client.post("/datasets/broker", json=broker_data())
    data = {
        "topic_name": f"topic-{uuid.uuid4().hex[:6]}",
        "topic_schema": {"key1": "value1", "key2": "value2"},
        "broker_id": broker_response.json()["data"]["id"],
    }

    response = test_client.post("/datasets/topic/register", json=data)
    if response.status_code == status.HTTP_201_CREATED:
        response = test_client.get("/datasets/topic/details")
        assert response.json()["status_code"] == status.HTTP_200_OK
        assert response.json()["message"] == "Topic Details."


def test_dataset_broker_topic_register(test_client):
    """
    Test successful broker topic registration.

    Args:
        test_client: The test client to use for making the request.

    Returns:
        The response status code is 201.
    """
    message_data = {
        "name": "test_ds",
        "description": "dataset test",
        "broker_id": "1",
        "topic_id": "1",
        "dataset_type": "1",
    }
    broker_response = test_client.post("/datasets/broker", json=broker_data())
    data = {
        "name": f"topic-{uuid.uuid4().hex[:6]}",
        "schema": {"key1": "value1", "key2": "value2"},
        "broker_id": broker_response.json()["data"]["id"],
    }

    test_client.post("/datasets/topic", json=data)
    response = test_client.post("/datasets/message", json=message_data)
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["message"] == "Dataset Broker Topic Details."


def test_dataset_broker_topic_register_bid_not_found(test_client):
    """
    broker topic registration for unknown broker id.

    Args:
        test_client: The test client to use for making the request.

    Returns:
        The response status code is 201.
    """
    bid = "100"
    data = {
        "name": "test_ds",
        "description": "dataset test",
        "broker_id": bid,
        "topic_id": "1",
        "dataset_type": 1,
    }
    response = test_client.post("/datasets/message", json=data)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == f"Broker with name {bid} not found."


def test_dataset_broker_topic_register_tid_not_found(test_client):
    """
    broker topic registration for unknown topic id.

    Args:
        test_client: The test client to use for making the request.

    Returns:
        The response status code is 201.
    """
    topic_id = "100"
    broker_response = test_client.post("/datasets/broker", json=broker_data())
    data = {
        "name": "test_ds",
        "description": "dataset test",
        "broker_id": broker_response.json()["data"]["id"],
        "topic_id": topic_id,
        "dataset_type": 1,
    }
    response = test_client.post("/datasets/message", json=data)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == f"Topic with name {topic_id} not found."


def test_fetch_dataset_message_details(test_client):
    """
    Test for successfully fetching dataset message details.

    Args:
        test_client: The test client to use for making the request.

    Returns:
        The response status code is 200.
    """

    broker_response = test_client.post("/datasets/broker", json=broker_data())
    data = {
        "name": f"topic-{uuid.uuid4().hex[:6]}",
        "schema": {"key1": "value1", "key2": "value2"},
        "broker_id": broker_response.json()["data"]["id"],
    }

    topic_response = test_client.post(
        f"/datasets/broker/{data['broker_id']}/topic", json=data
    )
    message_data = {
        "name": "test_ds",
        "description": "dataset test",
        "broker_id": broker_response.json()["data"]["id"],
        "topic_id": topic_response.json()["data"]["id"],
        "dataset_type": "1",
    }

    response = test_client.post("/datasets/message", json=message_data)
    if response.status_code == status.HTTP_201_CREATED:
        dataset_id = response.json()["data"]["dataset"]["id"]
        message_response = test_client.get(f"/datasets/{dataset_id}/message/details")
        assert message_response.status_code == status.HTTP_200_OK
        assert message_response.json()["message"] == "Dataset message details."


def test_fetch_dataset_message_details_not_found(test_client):
    """
    Test for un successfully fetching dataset message details.

    Args:
        test_client: The test client to use for making the request.

    Returns:
        The response status code is 404.
    """
    dataset_id = 1
    response = test_client.get(f"/datasets/{dataset_id}/message/details")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == f"Dataset not found for the id {dataset_id}"


def test_fetch_dataset_message_details_invalid_id(test_client):
    """
    Test for un successfully fetching dataset message details.

    Args:
        test_client: The test client to use for making the request.

    Returns:
        The response status code is 404.
    """
    dataset_id = -1
    response = test_client.get(f"/datasets/{dataset_id}/message/details")
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert response_data["detail"][0]["msg"] == "ensure this value is greater than 0"


def test_fetch_table_records_invalid_id(test_client):
    """
    Test for unsuccessful request with invalid dataset_id.

    Args:
        test_client: The test client to use for making the request.

    Returns:
        The response status code is 422.
    """
    dataset_id = -1
    response = test_client.get(f"/datasets/{dataset_id}/table/records")
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert response_data["detail"][0]["msg"] == "ensure this value is greater than 0"


def test_fetch_table_records_not_found(test_client):
    """
    Test for unsuccessful request with not found dataset_id.

    Args:
         test_client: The test client to use for making the request.

    Returns:
        The response status code is 404.
    """
    dataset_id = 100
    response = test_client.get(f"/datasets/{dataset_id}/table/records")
    response_data = response.json()
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response_data["detail"] == "Dataset not found."


def test_fetch_table_records_success(test_client):
    """
    Test for successful request with valid dataset_id.

    Args:
         test_client: The test client to use for making the request.

    Returns:
        The response status code is 200.
    """
    mocked_data = {
        "table_name": "model_info",
        "records": [
            {
                "id": 1,
                "name": "modeltest",
                "version": "1.0",
                "register_date": "2024-12-30T10:53:58.001112",
                "register_user_id": 0,
                "type": "keras",
                "description": "keras model",
                "last_modified_time": "2024-12-30T10:53:58.001115",
                "last_modified_user_id": 0,
            }
        ],
    }

    with patch(
        "app.services.dataset_service.DatasetService.fetch_table_records_for_dataset"
    ) as mock_search:
        mock_search.return_value = mocked_data

        response = test_client.get(
            "/datasets/1/table/records?limit=1",
            params={"dataset_id": "1"},
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["message"] == "Dataset Table Records"


def test_dataset_broker_update_invalid_data(test_client):
    """
    test for invalid broker update
      Args:
          test_client: The test client to use for making the request.

      Returns:
          The response status code is 422.

    """
    broker_id = -1
    response = test_client.patch(f"/datasets/broker/{broker_id}")
    response_data = response.json()
    print("broker patch", response_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert response_data["detail"][0]["msg"] == "ensure this value is greater than 0"


def test_dataset_broker_update_valid_data(test_client):
    """
       test for valid broker update
    Args:
        test_client: The test client to use for making the request.

    Returns:
        The response status code is 200.
    """
    broker_response = test_client.post("/datasets/broker", json=broker_data())
    broker_id = broker_response.json()["data"]["id"]

    if broker_response.status_code == status.HTTP_201_CREATED:
        response = test_client.patch(
            f"/datasets/broker/{broker_id}", json=broker_data()
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["message"] == "Broker updated successfully."


def test_dataset_broker_update_not_found(test_client):
    """
       test for not found  broker update
    Args:
        test_client: The test client to use for making the request.

    Returns:
        The response status code is 404.

    """
    broker_id = 900
    response = test_client.patch(f"/datasets/broker/{broker_id}", json=broker_data())
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == f"No BrokerDetails found for ID: {broker_id}"


def test_dataset_topic_update_invalid_data(test_client):
    """
    Test for invalid topic update where the topic ID is negative.

    Args:
        test_client: The test client to use for making the request.

    Returns:
        The response status code is 422.
    """
    topic_id = -1
    response = test_client.patch(f"/datasets/broker/topic/{topic_id}")
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert response_data["detail"][0]["msg"] == "ensure this value is greater than 0"


def test_dataset_topic_update_valid_data(test_client):
    """
    Test for a successful topic update.

    Args:
        test_client: The test client to use for making the request.

    Returns:
        The response status code is 200.
    """
    # Create a broker first
    broker_response = test_client.post("/datasets/broker", json=broker_data())
    broker_id = broker_response.json()["data"]["id"]

    # Create a topic under the broker
    topic_data = {
        "name": f"topic-{uuid.uuid4().hex[:6]}",
        "schema": {"key1": "value1", "key2": "value2"},
        "broker_id": broker_id,
    }
    topic_response = test_client.post(
        f"/datasets/broker/{broker_id}/topic", json=topic_data
    )
    print("topic_response", topic_response)
    topic_id = topic_response.json()["data"]["id"]

    # Prepare update data
    update_data = {
        "name": "updated_topic_name",
        "schema": {"new_key": "new_value"},
    }

    # Send update request
    response = test_client.patch(f"/datasets/broker/topic/{topic_id}", json=update_data)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["message"] == "Topic updated successfully."


def test_dataset_topic_update_not_found(test_client):
    """
    Test for topic update where the topic ID does not exist.

    Args:
        test_client: The test client to use for making the request.

    Returns:
        The response status code is 404.
    """
    topic_id = 12345  # Assume this topic ID does not exist
    update_data = {
        "name": "non_existent_topic",
        "schema": {"key": "value"},
    }
    response = test_client.patch(f"/datasets/broker/topic/{topic_id}", json=update_data)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == f"No TopicDetails found for ID: {topic_id}"


def test_fetch_datasets_topic_data_success(test_client):
    """
    Test for successful request with a valid dataset ID and limit.

    Args:
         test_client: The test client to use for making the request.

    Returns:
        The response status code should be 200.
    """
    mocked_result = {
        "dataset_id": 1,
        "records": [
            {"record_id": 1, "data": "sample data 1"},
            {"record_id": 2, "data": "sample data 2"},
        ],
        "record_count": 2,
        "topic_name": "test_topic",
        "topic_schema": "json",
    }

    with patch(
        "app.services.dataset_service.DatasetService.fetch_dataset_topic_data"
    ) as mock_fetch_data:
        mock_fetch_data.return_value = mocked_result

        response = test_client.get(
            "/datasets/1/topic/data?limit=10", params={"id": "1", "limit": 10}
        )

        # Assert response status and content
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["message"] == "Topic Data"
        assert len(response.json()["data"]["records"]) == 2
        assert response.json()["data"]["records"][0]["record_id"] == 1
        assert response.json()["data"]["records"][0]["data"] == "sample data 1"
        assert response.json()["data"]["topic_name"] == "test_topic"
        assert response.json()["data"]["topic_schema"] == "json"


def test_fetch_datasets_topic_data_not_found(test_client):
    """
    Test for handling a request where the dataset is not found.

    Args:
         test_client: The test client to use for making the request.

    Returns:
        The response status code should be 404.
    """
    with patch(
        "app.services.dataset_service.DatasetService.fetch_dataset_topic_data"
    ) as mock_fetch_data:
        # Simulate dataset not found by raising NoResultFound exception
        mock_fetch_data.side_effect = NoResultFound("Dataset not found.")

        response = test_client.get(
            "/datasets/11/topic/data?limit=10", params={"id": "11", "limit": 10}
        )

        # Assert response status and content
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()["detail"] == "Dataset not found."


def test_fetch_datasets_topic_data_internal_error(test_client):
    """
    Test for handling an internal server error.

    Args:
         test_client: The test client to use for making the request.

    Returns:
        The response status code should be 500.
    """
    with patch(
        "app.services.dataset_service.DatasetService.fetch_dataset_topic_data"
    ) as mock_fetch_data:
        # Simulate internal error by raising a generic exception
        mock_fetch_data.side_effect = Exception("Internal Server Error.")

        response = test_client.get(
            "/datasets/1/topic/data?limit=10", params={"id": "1", "limit": 10}
        )

        # Assert response status and content
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Internal Exception" in response.json()["detail"]


def test_fetch_datasets_topic_data_invalid_dataset_id(test_client):
    """
    Test for handling an invalid dataset ID (negative value).

    Args:
         test_client: The test client to use for making the request.

    Returns:
        The response status code should be 400 (Bad Request).
    """
    # Negative dataset ID (-1), which should be invalid
    response = test_client.get(
        "/datasets/-1/topic/data?limit=10", params={"id": "-1", "limit": 10}
    )

    # Assert response status and content
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert response.json()["detail"][0]["msg"] == "ensure this value is greater than 0"
