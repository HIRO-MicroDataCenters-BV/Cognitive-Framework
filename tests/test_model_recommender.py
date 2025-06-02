"""
Test Cases for fetch_model_recommend API endpoint.

This module contains unit tests for the model recommendation endpoint in a FastAPI application.
"""

from unittest.mock import patch

import pytest
from sqlalchemy.exc import NoResultFound

from app.schemas.model_recommender_info import ModelRecommendationOutput


def test_fetch_model_recommend_by_name(test_client):
    """
    Test fetch_model_recommend with valid model_name using GET request.
    Should return the best version of the specified model.
    """
    # Parameters for the GET request, passed as query parameters
    model_name = "Test_Model"

    # Mock the service method to return a specific recommendation when model_name is "Test_Model"
    with patch(
        "app.services.model_recommender_service.ModelRecommenderService.fetch_recommended_model_by_name"
    ) as mock_srv:
        # Simulate the output from the service (returning best model details)
        mock_srv.return_value = ModelRecommendationOutput(
            id=1,
            model_name="Test_Model",
            avg_f1_score=0.90,
            avg_accuracy=0.92,
            combined_score=0.91,  # Combined score remains
        )

        # Construct the query parameters for the GET request
        params = {
            "model_name": model_name,
        }

        # Call the API endpoint using GET with query parameters
        response = test_client.get("/models/recommend", params=params)

        # Assertions
        assert response.status_code == 200

        # Check the response content
        response_data = response.json()["data"]
        assert "data" in response.json()

        # Now check the individual fields
        assert response_data["model_name"]["model_name"] == "Test_Model"
        assert response_data["model_name"]["avg_f1_score"] == 0.90
        assert response_data["model_name"]["avg_accuracy"] == 0.92


def test_fetch_model_recommend_with_only_scores(test_client):
    """
    Test case 3: Only `classification_score` is provided.
    Should return the best model based on the provided classification scores.
    """
    classification_scores = ["accuracy_score", "f1_score"]

    # Mock the service method that fetches the best model based on classification scores
    with patch(
        "app.services.model_recommender_service.ModelRecommenderService."
        "fetch_recommended_model_by_classification_scores"
    ) as mock_service:
        # Simulated service return value
        mock_service.return_value = {
            "model_id": 2,
            "model_name": "Test_Model_1",
            "combined_score": 0.94,
            "scores": {
                "accuracy_score": 0.93,
                "f1_score": 0.95,
            },
            "cpu_percent": 40,
            "memory_percent": 1024,
        }

        # Make the GET request
        response = test_client.get(
            "/models/recommend", params={"classification_score": classification_scores}
        )

        # Assertions
        assert response.status_code == 200
        data = response.json()["data"]

        assert data["model_name"] == "Test_Model_1"
        assert data["combined_score"] == 0.94
        assert data["scores"]["accuracy_score"] == 0.93
        assert data["scores"]["f1_score"] == 0.95


def test_fetch_model_recommend_with_name_and_score(test_client):
    """
    Test case 1: Both `model_name` and `classification_score` are provided.
    Should return the best model recommendation based on the combination of both.
    """
    model_name = "Test_Model"
    classification_scores = ["f1_score", "accuracy_score"]

    # Mock the service method that fetches model by name and scores
    with patch(
        "app.services.model_recommender_service.ModelRecommenderService.fetch_best_model_by_name_and_scores"
    ) as mock_service:
        # Simulated service return value
        mock_service.return_value = {
            "model_id": 1,
            "model_name": "Test_Model",
            "combined_score": 0.95,
            "scores": {
                "f1_score": 0.94,
                "accuracy_score": 0.96,
            },
        }

        # Make the GET request
        response = test_client.get(
            "/models/recommend",
            params={
                "model_name": model_name,
                "classification_score": classification_scores,
            },
        )

        # Assertions
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["model_name"] == "Test_Model"
        assert data["combined_score"] == 0.95
        assert data["scores"]["f1_score"] == 0.94
        assert data["scores"]["accuracy_score"] == 0.96


def test_fetch_model_recommend_with_name_and_score_no_model_found(test_client):
    """
    Failure Scenario 1: No model found with the specified `model_name` and `classification_score`.
    The service should return a 404 error if no matching models are found.
    """
    model_name = "Non_Existent_Model"
    classification_scores = ["f1_score", "accuracy_score"]

    # Mock the service to raise NoResultFound, simulating no model found for the given name and scores
    with patch(
        "app.services.model_recommender_service.ModelRecommenderService.fetch_best_model_by_name_and_scores"
    ) as mock_service:
        mock_service.side_effect = NoResultFound("No suitable models found.")

        # Make the GET request
        response = test_client.get(
            "/models/recommend",
            params={
                "model_name": model_name,
                "classification_score": classification_scores,
            },
        )

        # Assertions: Check if the response returns a 404 status code
        assert response.status_code == 404
        assert response.json()["detail"] == "No model found with valid metrics."


def test_fetch_model_recommend_with_name_no_model_found(test_client):
    """
    Failure Scenario 2: No model found for the specified `model_name`.
    The service should return a 404 error if no matching model is found.
    """
    model_name = "Non_Existent_Model"

    # Mock the service to raise NoResultFound, simulating no model found for the given name
    with patch(
        "app.services.model_recommender_service.ModelRecommenderService.fetch_recommended_model_by_name"
    ) as mock_service:
        mock_service.side_effect = NoResultFound("No suitable model found.")

        # Make the GET request
        response = test_client.get(
            "/models/recommend", params={"model_name": model_name}
        )

        # Assertions: Check if the response returns a 404 status code
        assert response.status_code == 404
        assert response.json()["detail"] == "No model found with valid metrics."


@pytest.mark.asyncio
async def test_fetch_model_recommend_with_scores_no_model_found(test_client):
    """
    Failure Scenario 3: No model found for the specified `classification_score`.
    The service should return a 404 error if no matching models are found.
    """
    classification_scores = ["accuracy_score", "f1_score"]

    # Mock the service to raise NoResultFound, simulating no model found for the classification scores
    with patch(
        "app.services.model_recommender_service.ModelRecommenderService."
        "fetch_recommended_model_by_classification_scores"
    ) as mock_service:
        mock_service.side_effect = NoResultFound("No suitable models found.")

        # Make the GET request
        response = test_client.get(
            "/models/recommend", params={"classification_score": classification_scores}
        )

        # Assertions: Check if the response returns a 404 status code
        assert response.status_code == 404
        assert response.json()["detail"] == "No model found with valid metrics."
