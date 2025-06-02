"""
This module contains services for fetching and processing model recommendations.
"""

from typing import Optional
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import NoResultFound
from app.models.model_info import ModelInfo as ModelInfoDB
from app.schemas.model_recommender_info import ModelRecommendationOutput
from app.utils.exceptions import OperationException
from app.middleware.logger import logger

log = logger()


class ModelRecommenderService:
    """
    Service class responsible for recommending the best model based on either model name
    or by analyzing all available models based on their classification scores.

    Args:
        db_app (Session): The database session.

    Attributes:
        db_app (Session): The database session used for querying models.
    """

    def __init__(self, db_app: Session):
        """
        Initializes the ModelRecommenderService with the provided database session.

        Args:
            db_app (Session): The database session.
        """
        self.db_app = db_app

    def fetch_best_model_by_name_and_scores(
        self, model_name: str, classification_scores: List[str]
    ) -> Dict[str, Any]:
        """
        Fetch the best model with the given `model_name` based on the provided `classification_scores`.
        """
        try:
            models = (
                self.db_app.query(ModelInfoDB)
                .filter(ModelInfoDB.name == model_name)
                .all()
            )

            if not models:
                raise NoResultFound(f"No models found for the name: {model_name}.")

            best_model = None
            highest_combined_score = -1.0

            for model in models:
                metrics_list = model.model_validation_metrics

                if not metrics_list:  # Skip if no metrics are available
                    continue

                combined_score = 0.0
                score_count = 0
                individual_scores = {}

                # Initialize CPU and memory values
                total_cpu_utilization = 0.0
                total_memory_utilization = 0.0
                cpu_count = 0
                memory_count = 0

                # Calculate the combined score for the provided classification metrics
                for score_name in classification_scores:
                    score_value = None  # Reset score_value for each score_name

                    # Loop through each metrics object in metrics_list
                    for metrics in metrics_list:
                        score_value = getattr(metrics, score_name, None)

                        # If the score_value is found, break the loop
                        if score_value is not None:
                            break

                    # Debug logging for missing scores
                    if score_value is None:
                        continue  # Skip this score if it's missing

                    combined_score += score_value
                    score_count += 1
                    individual_scores[score_name] = score_value

                # Calculate the average CPU and memory utilization from the metrics
                for metrics in metrics_list:
                    cpu_utilization = getattr(metrics, "cpu_consumption", None)
                    memory_utilization = getattr(metrics, "memory_utilization", None)

                    if cpu_utilization is not None:
                        total_cpu_utilization += cpu_utilization
                        cpu_count += 1

                    if memory_utilization is not None:
                        total_memory_utilization += memory_utilization
                        memory_count += 1

                # Compute average CPU and memory utilization if available
                avg_cpu_utilization = (
                    total_cpu_utilization / cpu_count if cpu_count > 0 else 0.0
                )
                avg_memory_utilization = (
                    total_memory_utilization / memory_count if memory_count > 0 else 0.0
                )

                if score_count > 0:
                    avg_combined_score = combined_score / score_count

                    # Update best model if the current model's average score is higher
                    if avg_combined_score > highest_combined_score:
                        highest_combined_score = avg_combined_score
                        best_model = {
                            "model_id": model.id,
                            "model_name": model.name,
                            "combined_score": avg_combined_score,
                            "scores": individual_scores,
                            "avg_cpu_utilization": avg_cpu_utilization,  # Add CPU utilization
                            "avg_memory_utilization": avg_memory_utilization,  # Add Memory utilization
                        }

            if best_model:
                return best_model

            raise NoResultFound(
                f"No suitable models found for {model_name} based on the classification scores."
            )

        except NoResultFound as exc:
            log.error("No models found: %s", str(exc))
            raise NoResultFound(f"{str(exc)}")

        except Exception as exc:
            log.error("Unexpected error: %s", str(exc))
            raise OperationException(f"Unexpected error: {str(exc)}")

    def fetch_recommended_model_by_name(
        self, model_name: str
    ) -> ModelRecommendationOutput:
        """
        Fetches the best version of a specific model by name, considering all its versions.

        Args:
            model_name (str): The name of the model to search for.

        Returns:
            ModelRecommendationOutput: The model version with the highest combined score of f1_score and accuracy_score.

        Raises:
            NoResultFound: If no models found with the provided name.
        """
        try:
            # Fetch all versions of the model with the specified name
            models = (
                self.db_app.query(ModelInfoDB)
                .filter(ModelInfoDB.name == model_name)
                .all()
            )

            # If no models are found, raise an error
            if not models:
                raise NoResultFound(f"No models found with name {model_name}.")

            recommend_model = None
            highest_score = 0.0

            # Iterate over all versions of the model to find the best one
            for model in models:
                metrics = model.model_validation_metrics

                # Ensure metrics is an iterable, even if it's empty
                if metrics is None:
                    continue  # Skip to the next model if there are no metrics

                total_f1_score = 0
                total_accuracy = 0
                count = 0

                # Iterate over the metrics to calculate the average f1 and accuracy scores
                for metric in metrics:
                    # Check if f1_score and accuracy_score are valid
                    if (
                        metric.f1_score is not None
                        and metric.accuracy_score is not None
                    ):
                        total_f1_score += metric.f1_score
                        total_accuracy += metric.accuracy_score
                        count += 1

                # If we found valid scores, calculate the averages
                if count > 0:
                    avg_f1_score = total_f1_score / count
                    avg_accuracy = total_accuracy / count
                    combined_score = (avg_f1_score + avg_accuracy) / 2

                    # Check if this model version has a higher score than the previous best
                    if combined_score > highest_score:
                        highest_score = combined_score
                        recommend_model = ModelRecommendationOutput(
                            id=model.id,
                            model_name=model.name,
                            avg_f1_score=avg_f1_score,
                            avg_accuracy=avg_accuracy,
                            combined_score=combined_score,
                        )

            # If we found a recommended model, return it
            if recommend_model:
                return recommend_model

            # If no model had valid metrics, raise an error
            raise NoResultFound(f"No suitable model found for {model_name}.")

        except NoResultFound as exc:
            log.error("No models found: %s", str(exc))
            raise NoResultFound(f"{str(exc)}")
        except Exception as exc:
            log.error("Unexpected error: %s", str(exc))
            raise OperationException(f"Unexpected error: {str(exc)}")

    def fetch_recommended_model_by_classification_scores(
        self, classification_scores: List[str]
    ) -> Dict[str, Any]:
        """
        Fetches the best-performing model based on the provided classification scores.
        If only classification_score is provided, selects the best model according to that score.
        """
        try:
            models = self.db_app.query(ModelInfoDB).all()

            if not models:
                raise NoResultFound("No models found in the database.")

            best_model_scores: Dict[str, Any] = {
                "model_id": None,
                "model_name": None,
                "combined_score": 0.0,
                "scores": {},
                "cpu_percent": float("inf"),
                "memory_percent": float("inf"),
            }

            highest_combined_score = -1.0

            for model in models:
                metrics = model.model_validation_metrics

                if not metrics:
                    continue  # Skip models with no metrics

                total_score = 0.0
                score_count = 0
                model_scores = {}

                cpu_percent = getattr(metrics[0], "cpu_consumption", None)
                memory_percent = getattr(metrics[0], "memory_utilization", None)

                if cpu_percent is None or memory_percent is None:
                    continue

                for metric in metrics:
                    for score_name in classification_scores:
                        score_value = getattr(metric, score_name, None)
                        if score_value is not None:
                            total_score += score_value
                            score_count += 1
                            model_scores[score_name] = score_value

                if score_count > 0:
                    combined_score = total_score / score_count

                    if combined_score > highest_combined_score or (
                        combined_score == highest_combined_score
                        and (
                            cpu_percent < best_model_scores["cpu_percent"]
                            or (
                                cpu_percent == best_model_scores["cpu_percent"]
                                and memory_percent < best_model_scores["memory_percent"]
                            )
                        )
                    ):
                        highest_combined_score = combined_score
                        best_model_scores = {
                            "model_id": model.id,
                            "model_name": model.name,
                            "combined_score": combined_score,
                            "scores": model_scores,
                            "cpu_percent": cpu_percent,
                            "memory_percent": memory_percent,
                        }

            if best_model_scores["model_id"] is not None:
                return best_model_scores

            log.info("Best model scores: %s ", best_model_scores)
            raise NoResultFound(
                "No suitable models found based on the given classification scores."
            )

        except NoResultFound as exc:
            log.error("No suitable models found: %s", str(exc))
            raise NoResultFound(f"{str(exc)}")
        except Exception as exc:
            log.error("Unexpected error: %s", str(exc))
            raise OperationException(f"Unexpected error: {str(exc)}")

    def fetch_recommend_model(
        self,
        model_name: Optional[str] = None,
        classification_score: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Fetches the recommended model based on the provided parameters.
        If only model_name is provided, it fetches the best version of that specific model.
        If only classification_score is provided, it fetches the best overall model based on those scores.
        If neither is provided, it fetches the best overall model based on accuracy_score and f1_score.

        Args:
            model_name (optional): The name of the model to search for.
            classification_score (optional): A list of classification scores to consider.

        Returns:
            Dict[str, Any]: The recommended model based on the criteria specified.

        Raises:
            NoResultFound: If no suitable models found.
        """

        try:
            # Fetch all models from the database
            models = self.db_app.query(ModelInfoDB).all()

            if not models:
                raise NoResultFound("No models found in the database.")

            # Variables to track the best models
            best_model = None
            highest_combined_score = -1.0

            for model in models:
                metrics = model.model_validation_metrics

                if not metrics:
                    continue

                # Loop through the model's metrics to find the best based on requested scores
                total_f1_score = 0
                total_accuracy = 0
                count = 0

                for metric in metrics:
                    if classification_score:
                        # Custom logic for multiple scores (extend if necessary)
                        for score in classification_score:
                            if hasattr(metric, score):
                                count += 1
                                total_f1_score += (
                                    metric.f1_score if score == "f1_score" else 0
                                )
                                total_accuracy += (
                                    metric.accuracy_score
                                    if score == "accuracy_score"
                                    else 0
                                )
                    else:
                        # Default case: check accuracy and f1 score
                        count += 1
                        total_f1_score += metric.f1_score
                        total_accuracy += metric.accuracy_score

                # Calculate average score only if we have a count
                if count > 0:
                    avg_f1_score = total_f1_score / count
                    avg_accuracy = total_accuracy / count
                    combined_score = (avg_f1_score + avg_accuracy) / 2

                    # Update best model if this has a better combined score
                    if combined_score > highest_combined_score:
                        highest_combined_score = combined_score
                        best_model = {
                            "model_id": model.id,
                            "model_name": model.name,
                            "avg_f1_score": avg_f1_score,
                            "avg_accuracy": avg_accuracy,
                        }

            if best_model:
                return {
                    "model_id": best_model["model_id"],
                    "model_name": best_model["model_name"],
                    "avg_accuracy": best_model["avg_accuracy"],
                    "avg_f1_score": best_model["avg_f1_score"],
                }

            raise NoResultFound(
                "No suitable models found based on accuracy_score and f1_score."
            )

        except NoResultFound as exc:
            log.error("No suitable models found: %s", str(exc))
            raise NoResultFound(f"{str(exc)}")
        except Exception as exc:
            log.error("Unexpected error: %s", str(exc))
            raise OperationException(f"Unexpected error: {str(exc)}")
