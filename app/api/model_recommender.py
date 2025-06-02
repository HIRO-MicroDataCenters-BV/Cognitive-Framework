"""
API endpoints for model recommender system.
"""

from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import NoResultFound
from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.db.session import get_db
from app.schemas.response import StandardResponse
from app.services.model_recommender_service import ModelRecommenderService
from app.utils.response_utils import standard_response

router = APIRouter()


@router.get("/models/recommend", response_model=StandardResponse[Dict[str, Any]])
async def fetch_model_recommend(
    model_name: Optional[str] = Query(
        None, description="The name of the model to filter the recommendation."
    ),
    classification_score: Optional[List[str]] = Query(
        None,
        description=(
            "List of classification scores to consider"
            " (e.g., accuracy_score, f1_score, recall_score,"
            " log_loss, roc_auc, precision_score, example_count, score.). "
        ),
    ),
    db_app: Session = Depends(get_db),
):
    """
    API route to get the best model recommendation based on `model_name` and/or `classification_score`.

    This API endpoint can be used to fetch the best-performing machine learning model based on
    the model name, the classification scores (e.g., accuracy, f1_score), or both. The system
    returns the model with the highest average score when multiple classification scores are provided.

    Parameters:
    - `model_name` (optional): The name of the model to filter the recommendation.
      Example: "LR" (for Logistic Regression).
    - `classification_score` (optional): A list of classification metrics to rank models by.
      Possible values include accuracy_score, f1_score, recall_score, precision_score, etc.
      Example: "accuracy_score", "f1_score".
    - `db_app`: Database session.

    Returns:
    - The best model recommendation based on the specified criteria, including the model's ID,
      name, combined score (if multiple classification metrics are provided), and individual
      scores for each requested metric.

    Examples:

    1. **Example 1: When both `model_name` and `classification_score` are provided:**
       The API will filter models by `model_name` and then rank them based on the given `classification_score`.

    **Request:**
    ```
    GET /models/recommend?model_name=LR&classification_score=f1_score&classification_score=accuracy_score
    ```

    **Response:**
    ```json
    {
      "status_code": 200,
      "message": "Recommended Model",
      "data": {
        "model_id": 10,
        "model_name": "LR",
        "combined_score": 0.98,
        "scores": {
          "f1_score": 0.97,
          "accuracy_score": 0.99
        }
      }
    }
    ```

    2. **Example 2: When only `model_name` is provided:**
       The API will return the best version of the model based on general performance
       (e.g., average f1_score, accuracy).

    **Request:**
    ```
    GET /models/recommend?model_name=GradientBoosting
    ```

    **Response:**
    ```json
    {
      "status_code": 200,
      "message": "Recommended Model",
      "data": {
        "model_id": 12,
        "model_name": "Gradient Boosting",
        "avg_f1_score": 0.93,
        "avg_accuracy": 0.95
      }
    }
    ```


    Raises:
    - 404 Error: If no suitable models are found based on the provided criteria.
    - 500 Error: If an internal server error occurs during processing.
    """
    try:
        model_recommender_service = ModelRecommenderService(db_app)

        # Initialize an empty dictionary for the response data
        response_data = {}

        # Case 1: If both model_name and classification_score are provided
        if model_name and classification_score:
            best_model = model_recommender_service.fetch_best_model_by_name_and_scores(
                model_name=model_name,
                classification_scores=classification_score,
            )
            response_data = {
                "model_id": best_model.get("model_id"),
                "model_name": best_model.get("model_name"),
                "combined_score": best_model.get("combined_score"),
                "scores": best_model.get("scores"),
                "cpu_utilization": best_model.get(
                    "avg_cpu_utilization"
                ),  # Include CPU utilization
                "memory_utilization": best_model.get(
                    "avg_memory_utilization"
                ),  # Include Memory utilization
            }
        # Case 2: If only model_name is provided, find the best version of that model
        elif model_name:
            recommended_model = (
                model_recommender_service.fetch_recommended_model_by_name(
                    model_name=model_name
                )
            )

            if recommended_model:
                response_data["model_name"] = {
                    "model_id": recommended_model.id,
                    "model_name": recommended_model.model_name,
                    "avg_f1_score": recommended_model.avg_f1_score,
                    "avg_accuracy": recommended_model.avg_accuracy,
                }
            else:
                raise NoResultFound(f"No suitable model found for {model_name}.")

        # Case 3: If only classification_score is provided, fetch models based on scores
        elif classification_score:
            best_model = model_recommender_service.fetch_recommended_model_by_classification_scores(
                classification_scores=classification_score
            )

            response_data = {
                "model_id": best_model.get("model_id"),
                "model_name": best_model.get("model_name"),
                "combined_score": best_model.get("combined_score"),
                "scores": best_model.get("scores"),
            }

        # Case 4: If neither parameter is provided, get a general recommendation
        else:
            recommended_models = model_recommender_service.fetch_recommend_model()

            response_data = {
                "model_id": recommended_models.get("model_id"),
                "model_name": recommended_models.get("model_name"),
                "avg_f1_score": recommended_models.get("avg_f1_score"),
                "avg_accuracy": recommended_models.get("avg_accuracy"),
            }

        # Return the recommendation in the response
        return standard_response(
            status_code=200,
            message="Recommended Model",
            data=response_data,
        )

    # Handle cases where no models are found
    except NoResultFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No model found with valid metrics.",
        )
    # Handle any other exceptions
    except Exception as exp:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal Server Error: {str(exp)}",
        )
