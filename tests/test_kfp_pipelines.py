"""
Test cases for the kfp pipeline endpoints.
"""

import datetime
import json
import uuid
from sqlite3 import IntegrityError
from unittest.mock import patch

from fastapi import status

from config import constants as const


def test_post_pipeline_details_with_model_id_success(test_client):
    """
    GIVEN a application configured for testing
    WHEN the '/pipeline' API is requested (POST) with correct data
    THEN check the response shows a success result
    """
    # Arrange
    pipeline_uuid = str(uuid.uuid4())
    experiment_uuid = str(uuid.uuid4())
    run_uuid = str(uuid.uuid4())
    payload = {
        "run_details": {
            "uuid": run_uuid,
            "name": "kf_component_pipeline_cogflow_test ",
            "description": "Run of kf_component_pipeline_test (8eca6)",
            "experiment_uuid": experiment_uuid,
            "pipeline_uuid": pipeline_uuid,
            "createdAt_in_sec": "2024-05-28T13:16:35+00:00",
            "scheduledAt_in_sec": "2024-05-28T13:16:35+00:00",
            "finishedAt_in_sec": "2024-05-28T13:16:35+00:00",
            "state": "Succeeded",
        },
        "experiment_details": {
            "uuid": experiment_uuid,
            "name": "kfp_component_cogflow_test",
            "description": "kfp_component_cogflow_test",
            "createdatinSec": "2024-05-28T13:16:35+00:00",
        },
        "pipeline_details": {
            "uuid": pipeline_uuid,
            "createdAt_in_sec": "2024-05-28T13:16:35+00:00",
            "name": "kf_component_pipeline_test",
            "description": "kf_component_pipeline_test",
            "parameters": "null",
            "experiment_uuid": experiment_uuid,
        },
        "model_ids": [1],
        "task_details": [
            {
                "uuid": str(uuid.uuid4()),
                "name": "my-first-pipeline-tq62m",
                "state": "Succeeded",
                "runuuid": run_uuid,
                "startedtimestamp": "2024-05-28T13:16:35+00:00",
                "finishedtimestamp": "2024-05-28T13:16:35+00:00",
                "createdtimestamp": "2024-05-28T13:16:35+00:00",
            },
            {
                "uuid": str(uuid.uuid4()),
                "name": "compute-average",
                "state": "Succeeded",
                "runuuid": run_uuid,
                "startedtimestamp": "2024-05-28T13:16:35+00:00",
                "finishedtimestamp": "2024-05-28T13:16:35+00:00",
                "createdtimestamp": "2024-05-28T13:16:35+00:00",
            },
        ],
    }

    # breakpoint()
    # Act
    response = test_client.post("/pipeline", json=payload)

    # Assert
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["message"] == "Created new Pipeline details"
    assert "data" in response.json()


def test_post_pipeline_details_with_no_model_id_success(test_client):
    """
    GIVEN a application configured for testing
    WHEN the '/pipeline' API is requested (POST) with data with no model_id
    THEN check the response results in success
    """
    # Arrange
    pipeline_uuid = str(uuid.uuid4())
    experiment_uuid = str(uuid.uuid4())
    run_uuid = str(uuid.uuid4())
    payload = {
        "run_details": {
            "uuid": run_uuid,
            "name": "kf_component_pipeline_cogflow_test ",
            "description": "Run of kf_component_pipeline_test (8eca6)",
            "experiment_uuid": experiment_uuid,
            "pipeline_uuid": pipeline_uuid,
            "createdAt_in_sec": "2024-05-28T13:16:35+00:00",
            "scheduledAt_in_sec": "2024-05-28T13:16:35+00:00",
            "finishedAt_in_sec": "2024-05-28T13:16:35+00:00",
            "state": "Succeeded",
        },
        "experiment_details": {
            "uuid": experiment_uuid,
            "name": "kfp_component_cogflow_test",
            "description": "kfp_component_cogflow_test",
            "createdatinSec": "2024-05-28T13:16:35+00:00",
        },
        "pipeline_details": {
            "uuid": pipeline_uuid,
            "createdAt_in_sec": "2024-05-28T13:16:35+00:00",
            "name": "kf_component_pipeline_test",
            "description": "kf_component_pipeline_test",
            "parameters": "null",
            "experiment_uuid": experiment_uuid,
        },
        "model_ids": [],
        "task_details": [
            {
                "uuid": str(uuid.uuid4()),
                "name": "my-first-pipeline-tq62m",
                "state": "Succeeded",
                "runuuid": run_uuid,
                "startedtimestamp": "2024-05-28T13:16:35+00:00",
                "finishedtimestamp": "2024-05-28T13:16:35+00:00",
                "createdtimestamp": "2024-05-28T13:16:35+00:00",
            },
            {
                "uuid": str(uuid.uuid4()),
                "name": "compute-average",
                "state": "Succeeded",
                "runuuid": run_uuid,
                "startedtimestamp": "2024-05-28T13:16:35+00:00",
                "finishedtimestamp": "2024-05-28T13:16:35+00:00",
                "createdtimestamp": "2024-05-28T13:16:35+00:00",
            },
        ],
    }
    # pdb.set_trace()
    # Act
    response = test_client.post("/pipeline", json=payload)
    print("response .....", response.text)
    # Assert
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["message"] == "Created new Pipeline details"
    assert "data" in response.json()


@patch("app.services.kfp_pipeline_service.KfpPipelineService.upload_pipeline_details")
def test_post_pipeline_details_model_id_error(
    mock_upload_pipeline_details, test_client
):
    """
    GIVEN a application configured for testing
    WHEN the '/pipeline' API is requested (POST) with incorrect same data
    THEN check the response shows a error
    """
    # Arrange
    mock_upload_pipeline_details.side_effect = IntegrityError(
        "Database error: Integrity Error occurred"
    )
    payload = {
        "pipeline_details": {
            "uuid": "0d3ffa58-7d15-4456-a1f6-2c1355f95d22",
            "createdAt_in_sec": "2024-05-28T13:14:39+00:00",
            "name": "kf_component_pipeline_test",
            "description": "kf_component_pipeline_test",
            "parameters": "null",
            "experiment_uuid": "81e27097-e6c9-4ac4-ac9c-ed15afff182f",
            "pipeline_spec": "",
        }
    }

    # Act
    response = test_client.post("/pipeline", data=json.dumps(payload))

    # Assert
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert "detail" in response.json()
    assert (
        response.json()["detail"]
        == "Internal Server Error: Database error: Integrity Error occurred"
    )


@patch("app.services.kfp_pipeline_service.KfpPipelineService.get_pipeline_by_model_id")
def test_get_pipeline_by_model_id(mock_srv, test_client):
    """
    GIVEN a application configured for testing
    WHEN the '/pipeline/model_id/{model_id}' API is requested (GET) with valid model_id
    THEN check the response is valid and pipeline details are retrieved from service
    """

    mock_srv.return_value = [
        {
            "uuid": "0d3ffa58-7d15-4456-a1f6-2c1355f95d22",
            "name": "kf_component_pipeline_test",
            "model_id": 1,
            "description": "kf_component_pipeline_test",
            "createdAt_in_sec": "2024-05-28T13:14:39",
            "experiment_uuid": "81e27097-e6c9-4ac4-ac9c-ed15afff182f",
            "id": 12,
        }
    ]

    response = test_client.get("/pipeline/2")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["message"] == "Pipeline Details"
    assert "data" in response.json()


@patch("app.services.kfp_pipeline_service.KfpPipelineService.get_pipeline_by_model_id")
def test_get_pipeline_by_model_id_not_found(mock_srv, test_client):
    """
    GIVEN a application configured for testing
    WHEN the '/pipeline/model_id/{model_id}' API is requested (GET) with incorrect model_id
    THEN check the response is valid and corresponding error message is shown
    """

    mock_srv.side_effect = Exception(const.PIPELINE_MODEL_ID_ERROR_MSG)
    response = test_client.get("/pipeline/22")
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert "detail" in response.json()
    assert (
        response.json()["detail"]
        == f"Internal Server Error: {const.PIPELINE_MODEL_ID_ERROR_MSG}"
    )


@patch("app.services.kfp_pipeline_service.KfpPipelineService.list_runs_by_pipeline_id")
def test_get_run_details_by_pipeline_id(mock_srv, test_client):
    """
    GIVEN a application configured for testing
    WHEN the '/pipeline/runs/{pipeline_id}' API is requested (GET) with valid pipeline_id
    THEN check the response is valid and run  details are retrieved from service
    """

    mock_srv.return_value = [
        {
            "uuid": "02dc8c57-ce7c-4e33-9c0a-7ca9f137c7ef",
            "display_name": "kf_component_pipeline_cogflow_test ",
            "name": "kf_component_pipeline_cogflow_test ",
            "description": "Run of kf_component_pipeline_test (8eca6)",
            "experiment_uuid": "81e27097-e6c9-4ac4-ac9c-ed15afff182f",
            "pipeline_uuid": "0d3ffa58-7d15-4456-a1f6-2c1355f95d22",
            "createdAt_in_sec": "2024-05-28T13:16:35",
            "scheduledAt_in_sec": "2024-05-28T13:16:35",
            "finishedAt_in_sec": "2024-05-28T13:17:21",
            "state": "Succeeded",
        }
    ]
    response = test_client.get("/pipeline/runs/0d3ffa58-7d15-4456-a1f6-2c1355f95d22")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["message"] == "Run Details"
    assert "data" in response.json()
    for data in response.json()["data"]:
        assert "uuid" in data
        assert "display_name" in data
        assert "name" in data
        assert "description" in data
        assert "experiment_uuid" in data
        assert "pipeline_uuid" in data
        assert "state" in data
        assert "name" in data
        assert "name" in data


@patch("app.services.kfp_pipeline_service.KfpPipelineService.list_runs_by_pipeline_id")
def test_get_run_details_by_pipeline_id_not_found(mock_srv, test_client):
    """
    GIVEN a application configured for testing
    WHEN the '/pipeline/runs/{pipeline_id}' API is requested (GET) with invalid pipeline_id
    THEN check the response is valid and corresponding error message is shown
    """
    mock_srv.side_effect = Exception(const.RUN_NOT_FOUND)
    response = test_client.get("/pipeline/runs/22")
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response.json()["detail"] == f"Internal Server Error: {const.RUN_NOT_FOUND}"


@patch(
    "app.services.kfp_pipeline_service.KfpPipelineService.delete_runs_by_pipeline_id"
)
def test_delete_run_details_by_pipeline_id(mock_srv, test_client):
    """
    GIVEN a application configured for testing
    WHEN the '/pipeline/runs/{pipeline_id}' API is requested (DELETE) with valid pipeline_id
    THEN check the response is valid and deleted run details
    """
    mock_srv.return_value = [
        {
            "uuid": "02dc8c57-ce7c-4e33-9c0a-7ca9f137c7ef",
            "display_name": "kf_component_pipeline_cogflow_test ",
            "name": "kf_component_pipeline_cogflow_test ",
            "description": "Run of kf_component_pipeline_test (8eca6)",
            "experiment_uuid": "81e27097-e6c9-4ac4-ac9c-ed15afff182f",
            "pipeline_uuid": "0d3ffa58-7d15-4456-a1f6-2c1355f95d22",
            "createdAt_in_sec": "2024-05-28T13:16:35",
            "scheduledAt_in_sec": "2024-05-28T13:16:35",
            "finishedAt_in_sec": "2024-05-28T13:17:21",
            "state": "Succeeded",
        }
    ]
    pipeline_id = "0d3ffa58-7d15-4456-a1f6-2c1355f95d22"
    response = test_client.delete(f"/pipeline/runs/{pipeline_id}")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["message"] == "Run details deleted successfully"
    assert "data" in response.json()
    for data in response.json()["data"]:
        assert data["pipeline_uuid"] == pipeline_id


@patch(
    "app.services.kfp_pipeline_service.KfpPipelineService.delete_runs_by_pipeline_id"
)
def test_delete_run_details_by_pipeline_id_not_found(mock_srv, test_client):
    """
    GIVEN a application configured for testing
     WHEN the '/pipeline/runs/{pipeline_id}' API is requested (DELETE) with invalid pipeline_id
    THEN check the response is valid and corresponding error message is shown
    """

    mock_srv.side_effect = Exception(const.RUN_NOT_FOUND)
    response = test_client.delete("/pipeline/runs/2")
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response.json()["detail"] == f"Internal Server Error: {const.RUN_NOT_FOUND}"


@patch("app.services.kfp_pipeline_service.KfpPipelineService.delete_pipeline_details")
def test_delete_pipeline_details(mock_srv, test_client):
    """
    GIVEN a application configured for testing
    WHEN the '/pipeline/{pipeline_id}' API is requested (DELETE) with valid pipeline_id
    THEN check the response is valid and deleted pipeline details
    """
    mock_srv.return_value = [
        {
            "uuid": "0d3ffa58-7d15-4456-a1f6-2c1355f95d22",
            "model_id": 1,
            "name": "kf_component_pipeline_test",
            "description": "kf_component_pipeline_test",
            "createdAt_in_sec": "2024-05-28T13:14:39",
            "experiment_uuid": "81e27097-e6c9-4ac4-ac9c-ed15afff182f",
            "id": 12,
        }
    ]
    pipeline_id = "0d3ffa58-7d15-4456-a1f6-2c1355f95d22"
    response = test_client.delete(
        f"/pipeline/{pipeline_id}",
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["message"] == "Pipeline details deleted successfully"
    assert "data" in response.json()
    for data in response.json()["data"]:
        assert data["uuid"] == pipeline_id


@patch("app.services.kfp_pipeline_service.KfpPipelineService.delete_pipeline_details")
def test_delete_pipeline_details_not_found(mock_srv, test_client):
    """
    GIVEN a application configured for testing
     WHEN the '/pipeline/{pipeline_id}' API is requested (DELETE) with invalid pipeline_id
    THEN check the response is valid and corresponding error message is shown
    """

    mock_srv.side_effect = Exception(const.PIPELINE_ID_ERROR_MSG)
    response = test_client.delete("/pipeline/2")
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert (
        response.json()["detail"]
        == f"Internal Server Error: {const.PIPELINE_ID_ERROR_MSG}"
    )


@patch("cogflow.list_pipelines_by_name")
def test_list_pipelines_by_name(mock_srv, test_client):
    """
    GIVEN a application configured for testing
     WHEN the '/pipelines?pipeline_name={pipeline_name}' API is requested (GET)
    THEN check the response is valid
    """
    mock_srv.return_value = {
        "pipeline_id": "31a4694c-6da6-471d-b77a-2ec9ceefc2c2",
        "versions": [
            {
                "code_source_url": None,
                "created_at": datetime.datetime(2024, 6, 18, 0, 43, 17),
                "description": None,
                "id": "40e9371b-46cb-480d-844a-a0d9d64230a2",
                "name": "pipeline_vad_v1",
                "package_url": None,
                "parameters": [{"name": "url", "value": None}],
                "resource_references": [
                    {
                        "key": {
                            "id": "31a4694c-6da6-471d-b77a-2ec9ceefc2c2",
                            "type": "PIPELINE",
                        },
                        "name": None,
                        "relationship": "OWNER",
                    }
                ],
            }
        ],
        "runs": [
            {
                "createdAt_in_sec": "2024-05-28T13:16:35",
                "description": "Run of kf_component_pipeline_test (8eca6)",
                "display_name": "kf_component_pipeline_cogflow_test ",
                "experiment_uuid": "81e27097-e6c9-4ac4-ac9c-ed15afff182f7ab",
                "finishedAt_in_sec": "2024-05-28T13:17:21",
                "name": "kf_component_pipeline_cogflow_test ",
                "pipeline_uuid": "31a4694c-6da6-471d-b77a-2ec9ceefc2c2",
                "scheduledAt_in_sec": "2024-05-28T13:16:35",
                "state": "Succeeded",
                "uuid": "02dc8c57-ce7c-4e33-9c0a-7ca9f137c7ab",
            }
        ],
    }
    response = test_client.get("/pipelines?pipeline_name=kf_component_pipeline_test")
    assert response.status_code == 200


@patch("cogflow.list_pipelines_by_name")
def test_list_pipelines_by_name_no_runs(mock_srv, test_client):
    """
    GIVEN a application configured for testing
     WHEN the '/pipelines?pipeline_name={pipeline_name}' API is requested (GET) with no runs for pipeline
    THEN check the response is valid
    """
    mock_srv.return_value = {
        "pipeline_id": "31a4694c-6da6-471d-b77a-2ec9ceefc2c2",
        "versions": [
            {
                "code_source_url": None,
                "created_at": datetime.datetime(2024, 6, 18, 0, 43, 17),
                "description": None,
                "id": "40e9371b-46cb-480d-844a-a0d9d64230a2",
                "name": "pipeline_vad_v1",
                "package_url": None,
                "parameters": [{"name": "url", "value": None}],
                "resource_references": [
                    {
                        "key": {
                            "id": "31a4694c-6da6-471d-b77a-2ec9ceefc2c2",
                            "type": "PIPELINE",
                        },
                        "name": None,
                        "relationship": "OWNER",
                    }
                ],
            }
        ],
        "runs": [],
    }
    response = test_client.get("/pipelines?pipeline_name=kf_component_pipeline_test")
    assert response.status_code == 200


def test_list_pipelines_by_name_invalid_pipeline(test_client):
    """
    GIVEN a application configured for testing
     WHEN the '/pipelines?pipeline_name={pipeline_name}' API is requested (GET) with invalid pipeline
    THEN check the response status is 404 and error msg is returned
    """
    pipeline_name = "random_pipeline_name"
    response = test_client.get(f"/pipelines?pipeline_name={pipeline_name}")
    assert response.status_code == 404
    assert (
        response.json()["detail"] == f"pipeline with name '{pipeline_name}' not exists"
    )


@patch("cogflow.get_pipeline_task_sequence_by_pipeline_id")
def test_pipeline_component_by_pipeline_id(mock_srv, test_client):
    """
    GIVEN a application configured for testing
     WHEN the '/pipelines/component_by_pipeline_id/{pipeline_id}' API is requested (GET)
    THEN check the response is valid
    """
    data = [
        {
            "run_id": "e1e3560e-e895-4eb7-a35a-21e979e482ef",
            "pipeline_workflow_name": "test-pipeline-8bkfn",
            "task_structure": {
                "test-pipeline-8bkfn": {
                    "id": "test-pipeline-8bkfn",
                    "podName": "test-pipeline-8bkfn",
                    "name": "test-pipeline-8bkfn",
                    "inputs": [
                        {"name": "isvc", "value": ""},
                        {"name": "url", "value": ""},
                    ],
                    "outputs": [],
                    "status": "Failed",
                    "startedAt": "2024-10-11T09:39:24Z",
                    "finishedAt": "2024-10-11T09:39:34Z",
                    "resourcesDuration": {"cpu": 3, "memory": 2},
                    "children": [
                        {
                            "id": "test-pipeline-8bkfn-3395021217",
                            "podName": "test-pipeline-8bkfn-3395021217",
                            "name": "download-data",
                            "inputs": [{"name": "url", "value": ""}],
                            "outputs": {
                                "artifacts": [
                                    {
                                        "name": "download-data-Data",
                                        "path": "/tmp/outputs/Data/data",
                                    }
                                ],
                                "exitCode": "3",
                            },
                            "status": "Failed",
                            "startedAt": "2024-10-11T09:39:24Z",
                            "finishedAt": "2024-10-11T09:39:28Z",
                            "resourcesDuration": {"cpu": 3, "memory": 2},
                            "children": [
                                {
                                    "id": "test-pipeline-8bkfn-536067876",
                                    "podName": "test-pipeline-8bkfn-536067876",
                                    "name": "preprocess",
                                    "inputs": [],
                                    "outputs": [],
                                    "status": "Omitted",
                                    "startedAt": "2024-10-11T09:39:34Z",
                                    "finishedAt": "2024-10-11T09:39:34Z",
                                    "resourcesDuration": {},
                                    "children": [
                                        {
                                            "id": "test-pipeline-8bkfn-910161396",
                                            "podName": "test-pipeline-8bkfn-910161396",
                                            "name": "training",
                                            "inputs": [],
                                            "outputs": [],
                                            "status": "Omitted",
                                            "startedAt": "2024-10-11T09:39:34Z",
                                            "finishedAt": "2024-10-11T09:39:34Z",
                                            "resourcesDuration": {},
                                            "children": [
                                                {
                                                    "id": "test-pipeline-8bkfn-1897524482",
                                                    "podName": "test-pipeline-8bkfn-1897524482",
                                                    "name": "serving",
                                                    "inputs": [],
                                                    "outputs": [],
                                                    "status": "Omitted",
                                                    "startedAt": "2024-10-11T09:39:34Z",
                                                    "finishedAt": "2024-10-11T09:39:34Z",
                                                    "resourcesDuration": {},
                                                    "children": [
                                                        {
                                                            "id": "test-pipeline-8bkfn-2798586311",
                                                            "podName": "test-pipeline-8bkfn-2798586311",
                                                            "name": "getmodel",
                                                            "inputs": [],
                                                            "outputs": [],
                                                            "status": "Omitted",
                                                            "startedAt": "2024-10-11T09:39:34Z",
                                                            "finishedAt": "2024-10-11T09:39:34Z",
                                                            "resourcesDuration": {},
                                                            "children": [],
                                                        }
                                                    ],
                                                }
                                            ],
                                        }
                                    ],
                                }
                            ],
                        }
                    ],
                }
            },
        },
        {
            "run_id": "d4e819e3-b963-4860-b7f0-96b3b0472546",
            "pipeline_workflow_name": "test-pipeline-m56cp",
            "task_structure": {
                "test-pipeline-m56cp": {
                    "id": "test-pipeline-m56cp",
                    "podName": "test-pipeline-m56cp",
                    "name": "test-pipeline-m56cp",
                    "inputs": [
                        {"name": "isvc", "value": "sample-final-bola-verge332"},
                        {
                            "name": "url",
                            "value": "https://raw.githubusercontent.com/Barteus/kubeflow-examples/main"
                            "/e2e-wine-kfp-mlflow/winequality-red.csv",
                        },
                    ],
                    "outputs": [],
                    "status": "Failed",
                    "startedAt": "2024-10-11T09:40:21Z",
                    "finishedAt": "2024-10-11T09:41:12Z",
                    "resourcesDuration": {"cpu": 40, "memory": 29},
                    "children": [
                        {
                            "id": "test-pipeline-m56cp-2186394041",
                            "podName": "test-pipeline-m56cp-2186394041",
                            "name": "download-data",
                            "inputs": [
                                {
                                    "name": "url",
                                    "value": "https://raw.githubusercontent.com/Barteus/kubeflow-examples/main"
                                    "/e2e-wine-kfp-mlflow/winequality-red.csv",
                                }
                            ],
                            "outputs": {
                                "artifacts": [
                                    {
                                        "name": "download-data-Data",
                                        "path": "/tmp/outputs/Data/data",
                                        "s3": {
                                            "key": "test-pipeline-m56cp/test-pipeline-m56cp-2186394041"
                                            "/download-data-Data.tgz"
                                        },
                                    }
                                ],
                                "exitCode": "0",
                            },
                            "status": "Succeeded",
                            "startedAt": "2024-10-11T09:40:21Z",
                            "finishedAt": "2024-10-11T09:40:26Z",
                            "resourcesDuration": {"cpu": 4, "memory": 2},
                            "children": [
                                {
                                    "id": "test-pipeline-m56cp-25504140",
                                    "podName": "test-pipeline-m56cp-25504140",
                                    "name": "preprocess",
                                    "inputs": [],
                                    "outputs": {
                                        "artifacts": [
                                            {
                                                "name": "preprocess-output",
                                                "path": "/tmp/outputs/output/data",
                                                "s3": {
                                                    "key": "test-pipeline-m56cp/test-pipeline-m56cp-25504140"
                                                    "/preprocess-output.tgz"
                                                },
                                            }
                                        ],
                                        "exitCode": "0",
                                    },
                                    "status": "Succeeded",
                                    "startedAt": "2024-10-11T09:40:31Z",
                                    "finishedAt": "2024-10-11T09:40:36Z",
                                    "resourcesDuration": {"cpu": 3, "memory": 2},
                                    "children": [
                                        {
                                            "id": "test-pipeline-m56cp-3689243468",
                                            "podName": "test-pipeline-m56cp-3689243468",
                                            "name": "training",
                                            "inputs": [],
                                            "outputs": {
                                                "parameters": [
                                                    {
                                                        "name": "training-Output",
                                                        "value": "s3://mlflow/0/269438ce47e64527afe87e5cae93caef"
                                                        "/artifacts/model",
                                                        "valueFrom": {
                                                            "path": "/tmp/outputs/Output/data"
                                                        },
                                                    }
                                                ],
                                                "artifacts": [
                                                    {
                                                        "name": "training-Output",
                                                        "path": "/tmp/outputs/Output/data",
                                                        "s3": {
                                                            "key": "test-pipeline-m56cp/test-pipeline-m56cp-3689243468"
                                                            "/training-Output.tgz"
                                                        },
                                                    }
                                                ],
                                                "exitCode": "0",
                                            },
                                            "status": "Succeeded",
                                            "startedAt": "2024-10-11T09:40:42Z",
                                            "finishedAt": "2024-10-11T09:40:56Z",
                                            "resourcesDuration": {
                                                "cpu": 24,
                                                "memory": 18,
                                            },
                                            "children": [
                                                {
                                                    "id": "test-pipeline-m56cp-1253916586",
                                                    "podName": "test-pipeline-m56cp-1253916586",
                                                    "name": "serving",
                                                    "inputs": [
                                                        {
                                                            "name": "isvc",
                                                            "value": "sample-final-bola-verge332",
                                                        },
                                                        {
                                                            "name": "training-Output",
                                                            "value": "s3://mlflow/0/269438ce47e64527afe87e5cae93caef"
                                                            "/artifacts/model",
                                                        },
                                                    ],
                                                    "outputs": {"exitCode": "1"},
                                                    "status": "Failed",
                                                    "startedAt": "2024-10-11T09:41:02Z",
                                                    "finishedAt": "2024-10-11T09:41:09Z",
                                                    "resourcesDuration": {
                                                        "cpu": 9,
                                                        "memory": 7,
                                                    },
                                                    "children": [
                                                        {
                                                            "id": "test-pipeline-m56cp-3537241551",
                                                            "podName": "test-pipeline-m56cp-3537241551",
                                                            "name": "getmodel",
                                                            "inputs": [],
                                                            "outputs": [],
                                                            "status": "Omitted",
                                                            "startedAt": "2024-10-11T09:41:12Z",
                                                            "finishedAt": "2024-10-11T09:41:12Z",
                                                            "resourcesDuration": {},
                                                            "children": [],
                                                        }
                                                    ],
                                                }
                                            ],
                                        }
                                    ],
                                }
                            ],
                        }
                    ],
                }
            },
        },
    ]
    mock_srv.return_value = data
    pipeline_id = "1000537e-b101-4432-a779-768ec479c2b0"
    response = test_client.get(f"/pipelines/component?pipeline_id={pipeline_id}")
    assert response.status_code == 200


@patch("cogflow.get_pipeline_task_sequence_by_pipeline_id")
def test_pipeline_component_by_pipeline_id_error(mock_srv, test_client):
    """
    GIVEN a application configured for testing
     WHEN the '/pipelines/component_by_pipeline_id/{pipeline_id}' API is requested (GET)
    THEN check the response is 404 when ValueError is raised
    """
    mock_srv.side_effect = ValueError("pipeline_id not found")
    pipeline_id = "1000537e-b101-4432-a779-768ec479c2b0"
    response = test_client.get(f"/pipelines/component?pipeline_id={pipeline_id}")
    assert response.status_code == 404
    assert response.json()["detail"] == "pipeline_id not found"


@patch("cogflow.get_pipeline_task_sequence_by_run_id")
def test_pipeline_component_by_run_id(mock_srv, test_client):
    """
    GIVEN a application configured for testing
     WHEN the '/pipelines/component_by_run_id/{run_id}' API is requested (GET)
    THEN check the response is valid
    """
    pipeline_workflow_name = "wp3ex-x72sj"
    task_structure = {
        "wp3ex-x72sj": {
            "id": "wp3ex-x72sj",
            "podName": "wp3ex-x72sj",
            "name": "wp3ex-x72sj",
            "inputs": [{"name": "datasetname", "value": "openb_pod_list_default"}],
            "outputs": [],
            "status": "Succeeded",
            "startedAt": "2024-09-09T16:57:53Z",
            "finishedAt": "2024-09-09T17:06:22Z",
            "resourcesDuration": {"cpu": 1252, "memory": 1015},
            "children": [
                {
                    "id": "wp3ex-x72sj-3184817070",
                    "podName": "wp3ex-x72sj-3184817070",
                    "name": "load-dataset",
                    "inputs": [
                        {"name": "datasetname", "value": "openb_pod_list_default"}
                    ],
                    "outputs": {
                        "artifacts": [
                            {
                                "name": "load-dataset-dataset",
                                "path": "/tmp/outputs/dataset/data",
                                "s3": {
                                    "key": "wp3ex-x72sj/wp3ex-x72sj-3184817070/load-dataset-dataset.tgz"
                                },
                            }
                        ],
                        "exitCode": "0",
                    },
                    "status": "Succeeded",
                    "startedAt": "2024-09-09T16:57:53Z",
                    "finishedAt": "2024-09-09T16:57:57Z",
                    "resourcesDuration": {"cpu": 3, "memory": 2},
                }
            ],
        }
    }
    mock_srv.return_value = pipeline_workflow_name, task_structure
    run_id = "random_run_id"
    response = test_client.get(f"/pipelines/component/run?run_id={run_id}")
    assert response.status_code == 200


@patch("cogflow.get_pipeline_task_sequence_by_run_id")
def test_pipeline_component_by_run_id_error(mock_srv, test_client):
    """
    GIVEN a application configured for testing
     WHEN the '/pipelines/component_by_run_id/{run_id}' API is requested (GET)
    THEN check the response is 404 when ValueError is raised
    """
    mock_srv.side_effect = ValueError("run_id not found")
    run_id = "random_run_id"
    response = test_client.get(f"/pipelines/component/run?run_id={run_id}")
    assert response.status_code == 404
    assert response.json()["detail"] == "run_id not found"


@patch("cogflow.get_pipeline_task_sequence_by_run_name")
def test_pipeline_component_by_run_name(mock_srv, test_client):
    """
    GIVEN a application configured for testing
     WHEN the '/pipelines/component_by_run_name?run_name={run_name}' API is requested (GET)
    THEN check the response is valid
    """
    pipeline_workflow_name = "wp3ex-x72sj"
    task_structure = {
        "wp3ex-x72sj": {
            "id": "wp3ex-x72sj",
            "podName": "wp3ex-x72sj",
            "name": "wp3ex-x72sj",
            "inputs": [{"name": "datasetname", "value": "openb_pod_list_default"}],
            "outputs": [],
            "status": "Succeeded",
            "startedAt": "2024-09-09T16:57:53Z",
            "finishedAt": "2024-09-09T17:06:22Z",
            "resourcesDuration": {"cpu": 1252, "memory": 1015},
            "children": [
                {
                    "id": "wp3ex-x72sj-3184817070",
                    "podName": "wp3ex-x72sj-3184817070",
                    "name": "load-dataset",
                    "inputs": [
                        {"name": "datasetname", "value": "openb_pod_list_default"}
                    ],
                    "outputs": {
                        "artifacts": [
                            {
                                "name": "load-dataset-dataset",
                                "path": "/tmp/outputs/dataset/data",
                                "s3": {
                                    "key": "wp3ex-x72sj/wp3ex-x72sj-3184817070/load-dataset-dataset.tgz"
                                },
                            }
                        ],
                        "exitCode": "0",
                    },
                    "status": "Succeeded",
                    "startedAt": "2024-09-09T16:57:53Z",
                    "finishedAt": "2024-09-09T16:57:57Z",
                    "resourcesDuration": {"cpu": 3, "memory": 2},
                }
            ],
        }
    }
    mock_srv.return_value = pipeline_workflow_name, task_structure
    run_name = "random_run_name"
    response = test_client.get(f"/pipelines/component/run?run_name={run_name}")
    assert response.status_code == 200


@patch("cogflow.get_pipeline_task_sequence_by_run_name")
def test_pipeline_component_by_run_name_error(mock_srv, test_client):
    """
    GIVEN a application configured for testing
     WHEN the '/pipelines/component_by_run_name?run_name={run_name}' API is requested (GET)
    THEN check the response is 404 when ValueError is raised
    """
    mock_srv.side_effect = ValueError("run_id not found")
    run_name = "random_run_name"
    response = test_client.get(f"/pipelines/component/run?run_name={run_name}")
    assert response.status_code == 404
    assert response.json()["detail"] == "run_id not found"


@patch("cogflow.get_task_structure_by_task_id")
def test_pipeline_task_by_task_id(mock_srv, test_client):
    """
    GIVEN a application configured for testing
     WHEN the '/pipelines/task_by_task_id?task_id={task_id}' API is requested (GET)
    THEN check the response is valid
    """
    data = [
        {
            "id": "test-pipeline-749dn-2534915009",
            "name": "serving",
            "inputs": [
                {"name": "isvc", "value": "sample-final-bola-verge332"},
                {
                    "name": "training-Output",
                    "value": "s3://mlflow/0/eccd7757228f4419894c37d2721321ea/artifacts/model",
                },
            ],
            "outputs": {"exitCode": "0"},
            "status": "Succeeded",
            "startedAt": "2024-10-14T07:58:51Z",
            "finishedAt": "2024-10-14T07:59:08Z",
            "resourcesDuration": {"cpu": 30, "memory": 24},
            "run_id": "afcf98bb-a9af-4a34-a512-1236110150ae",
        }
    ]
    mock_srv.return_value = data
    task_id = "random_task_id"
    response = test_client.get(f"/pipelines/task?task_id={task_id}")
    assert response.status_code == 200


@patch("cogflow.get_task_structure_by_task_id")
def test_pipeline_task_by_task_id_error(mock_srv, test_client):
    """
    GIVEN a application configured for testing
     WHEN the '/pipelines/task_by_task_id?task_id={task_id}' API is requested (GET)
    THEN check the response is 404 when ValueError is raised
    """
    mock_srv.side_effect = ValueError("task_id not found")
    task_id = "random_task_id"
    response = test_client.get(f"/pipelines/task?task_id={task_id}")
    assert response.status_code == 404
    assert response.json()["detail"] == "task_id not found"
