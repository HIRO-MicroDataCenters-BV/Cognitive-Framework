"""
Test validation metrics and artifacts apis for the application.

Functions:
    test_register_model: Tests the model registration endpoint.
    test_get_models: Tests the model retrieval endpoint.
"""

from unittest.mock import patch

from fastapi import status


def test_upload_metric_details(test_client):
    """
        test the api POST "/validation/metrics"
    :param test_client:
    :return:
    """
    data = {
        "model_name": "Federated Learning1",
        "dataset_id": 1,
        "accuracy_score": 1,
        "example_count": 2,
        "f1_score": 2,
        "log_loss": 9,
        "precision_score": 8,
        "recall_score": 9,
        "roc_auc": 8,
        "score": 0.98,
    }

    with patch(
        "app.services.validation_service.ValidationService.upload_metrics_details"
    ) as mock_srv:
        # test for success operation
        mock_srv.return_value = [
            {
                "model_id": 1,
                "dataset_id": 1,
                "registered_date_time": "2024-08-27T21:17:29.473135",
                "accuracy_score": 0.98,
                "example_count": 50,
                "f1_score": 0.98,
                "log_loss": 0.046935737531967704,
                "precision_score": 0.98125,
                "recall_score": 0.98,
                "roc_auc": 1,
                "score": 0.98,
                "id": 34,
            }
        ]
        response = test_client.post(
            "/models",
            json={
                "name": "test_model",
                "version": "1.0",
                "register_user_id": 1,
                "type": "test",
                "description": "A test model",
            },
        )

        response = test_client.post("/validation/metrics", json=data)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["message"] == "Created new metric details."
        assert "data" in response.json()
        assert len(response.json()["data"]) == len(mock_srv.return_value)

        # test when Exception is raised
        mock_srv.side_effect = Exception("Error occurred")
        response = test_client.post("/validation/metrics", json=data)
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.json()["detail"] == "Internal Server Error: Error occurred"


def test_get_metrics_details(test_client):
    """
        test api GET "/validation/metrics"
    :param test_client:
    :return:
    """
    # input data
    model_id = 1
    model_name = "Federated Learning"

    with patch(
        "app.services.validation_service.ValidationService.get_metrics_details"
    ) as mock_srv:
        mock_srv.return_value = [
            {
                "model_id": 1,
                "dataset_id": 1,
                "registered_date_time": "2024-08-27T21:17:29.473135",
                "accuracy_score": 0.98,
                "example_count": 50,
                "f1_score": 0.98,
                "log_loss": 0.046935737531967704,
                "precision_score": 0.98125,
                "recall_score": 0.98,
                "roc_auc": 1,
                "score": 0.98,
                "id": 34,
            }
        ]
        response = test_client.get(
            f"/validation/metrics?model_id={model_id}&model_name={model_name}"
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["message"] == "Validation Metric Details"
        assert "data" in response.json()
        for data in response.json()["data"]:
            assert "id" in data
            assert "model_id" in data
            assert "dataset_id" in data

        # test in case of exception is raised
        mock_srv.side_effect = Exception("some error occurred")
        response = test_client.get(
            f"/validation/metrics?model_id={model_id}&model_name={model_name}"
        )
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.json()["detail"] == "Internal Server Error: some error occurred"


def test_get_metrics_details_no_data_found(test_client):
    """
        test api GET "/validation/metrics for no data found"
    :param test_client:
    :return:
    """
    # input data
    model_id = -1
    model_name = "Federated Learning"

    response = test_client.get(
        f"/validation/metrics?model_id={model_id}&model_name={model_name}"
    )

    print(response.json())
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert response.json()["detail"][0]["msg"] == "ensure this value is greater than 0"


def test_upload_validation_artifact(test_client):
    """
        test for api POST "/validation/artifact"
    :param test_client:
    :return:
    """
    # input data
    data = {
        "model_name": "Federated Learning",
        "dataset_id": "4",
        "validation_artifacts": {
            "roc_curve_plot": "s3://mlflow/0/8338e0f4/artifacts/roc_curve_plot.png",
            "precision_recall_curve_plot": "s3://mlflow/0/8338e0f4/artifacts/precision_recall_curve_plot.png",
            "per_class_metrics": "s3://mlflow/0/8338e0f4/artifacts/per_class_metrics.csv",
            "confusion_matrix": "s3://mlflow/0/8338e0f4/artifacts/confusion_matrix.png",
            "shap_beeswarm_plot": "s3://mlflow/0/8338e0f4/artifacts/shap_beeswarm_plot.png",
            "shap_summary_plot": "s3://mlflow/0/8338e0f4/artifacts/shap_summary_plot.png",
            "shap_feature_importance_plot": "s3://mlflow/0/8338e0f4/artifacts/shap_feature_importance_plot.png",
        },
    }
    with patch(
        "app.services.validation_service.ValidationService.save_validation_artifact"
    ) as mock_srv:
        mock_srv.return_value = [
            {
                "model_id": 1,
                "dataset_id": 1,
                "validation_artifacts": {
                    "roc_curve_plot": "s3://mlflow/0/8338e0f4/artifacts/roc_curve_plot.png",
                    "precision_recall_curve_plot": "s3://mlflow/0/8338e0f4/artifacts/precision_recall_curve_plot.png",
                    "per_class_metrics": "s3://mlflow/0/8338e0f4/artifacts/per_class_metrics.csv",
                    "confusion_matrix": "s3://mlflow/0/8338e0f4/artifacts/confusion_matrix.png",
                    "shap_beeswarm_plot": "s3://mlflow/0/8338e0f4/artifacts/shap_beeswarm_plot.png",
                    "shap_summary_plot": "s3://mlflow/0/8338e0f4/artifacts/shap_summary_plot.png",
                    "shap_feature_importance_plot": "s3://mlflow/0/8338e0f4/artifacts/shap_feature_importance_plot.png",
                },
                "id": 14,
            }
        ]
        response = test_client.post("/validation/artifact", json=data)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["message"] == "Validation Artifact Details"
        assert "data" in response.json()
        assert len(response.json()["data"]) == len(mock_srv.return_value)

        # test when Exception is raised
        mock_srv.side_effect = Exception("Error occurred")
        response = test_client.post("/validation/artifact", json=data)
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.json()["detail"] == "Internal Server Error: Error occurred"


def test_get_artifacts_details(test_client):
    """
        test for api GET "/validation/artifact"
    :param test_client:
    :return:
    """
    # input data
    model_id = 1
    model_name = "Federated Learning"

    with patch(
        "app.services.validation_service.ValidationService.get_artifacts_details"
    ) as mock_srv:
        mock_srv.return_value = [
            {
                "model_id": 1,
                "dataset_id": 1,
                "validation_artifacts": {
                    "roc_curve_plot": "s3://mlflow/0/8338e0f4/artifacts/roc_curve_plot.png",
                    "precision_recall_curve_plot": "s3://mlflow/0/8338e0f4/artifacts/precision_recall_curve_plot.png",
                    "per_class_metrics": "s3://mlflow/0/8338e0f4/artifacts/per_class_metrics.csv",
                    "confusion_matrix": "s3://mlflow/0/8338e0f4/artifacts/confusion_matrix.png",
                    "shap_beeswarm_plot": "s3://mlflow/0/8338e0f4/artifacts/shap_beeswarm_plot.png",
                    "shap_summary_plot": "s3://mlflow/0/8338e0f4/artifacts/shap_summary_plot.png",
                    "shap_feature_importance_plot": "s3://mlflow/0/8338e0f4/artifacts/shap_feature_importance_plot.png",
                },
                "id": 14,
            }
        ]
        response = test_client.get(
            f"/validation/artifacts?model_id={model_id}&model_name={model_name}"
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["message"] == "Validation Artifact Details"
        assert "data" in response.json()
        for data in response.json()["data"]:
            assert "id" in data
            assert "model_id" in data
            assert "dataset_id" in data

        # test in case of exception is raised
        mock_srv.side_effect = Exception("some error occurred")
        response = test_client.get(
            f"/validation/artifacts?model_id={model_id}&model_name={model_name}"
        )
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.json()["detail"] == "Internal Server Error: some error occurred"


def test_get_artifacts_details_no_data_found(test_client):
    """
        test for api GET "/validation/artifact for no data found"
    :param test_client:
    :return:
    """
    # input data
    model_id = -1
    model_name = "Federated Learning"

    response = test_client.get(
        f"/validation/artifacts?model_id={model_id}&model_name={model_name}"
    )
    print(response)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert response.json()["detail"][0]["msg"] == "ensure this value is greater than 0"
