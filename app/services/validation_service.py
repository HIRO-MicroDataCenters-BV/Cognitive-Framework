"""
Service for saving and retrieving validation metrics and artifacts.

This module provides a service class for saving and retrieving validation metrics and artifacts from the database.
"""

import importlib
import os
from typing import List

from sqlalchemy.exc import NoResultFound, IntegrityError
from sqlalchemy.orm import Session

from app.middleware.logger import logger
from app.models.model_dataset import ModelDataset as ModelDatasetDB
from app.models.model_info import ModelInfo as ModelInfoDB
from app.models.validation_artifact_info import (
    ValidationArtifact as ValidationArtifactDB,
)
from app.models.validation_metric_info import ValidationMetric as ValidationMetricDB
from app.schemas.validation_artifact_info import (
    ValidationArtifact,
    ValidationArtifactInput,
)
from app.schemas.validation_metric_info import ValidationMetric, ValidationMetricInput
from app.utils.exceptions import OperationException, ValidationException
from config import constants

log = logger()


class ValidationService:
    """
    Service class for saving and retrieving validation metrics and artifacts.
    """

    def __init__(self, db_app: Session):
        """
        Initialize the service with a database session and configuration.

        Args:
            db_app (Session): The database session.
        """
        config_type = os.getenv(
            "CONFIG_TYPE", default="config.app_config.DevelopmentConfig"
        )
        config_module, config_class = config_type.rsplit(".", 1)
        self.config = getattr(importlib.import_module(config_module), config_class)()
        self.db_app = db_app

    def get_metrics_details(
        self, model_pk=None, model_name=None
    ) -> List[ValidationMetric]:
        """
        Retrieve validation metric details based on provided filters.

        Args:
            model_pk (int, optional): The ID of the model to retrieve. Defaults to None.
            model_name (str, optional): The name of the model to retrieve. Defaults to None.

        Returns:
            List[ValidationMetric]: The list of validation metrics matching the filters.

        Raises:
            OperationException: If there is an unexpected error.
        """
        try:
            query = self.db_app.query(ValidationMetricDB)
            ids: List[int] = [0]
            if model_pk:
                query = query.filter(ValidationMetricDB.model_id == model_pk)
            if model_name:
                model_infos: List[ModelInfoDB] = (
                    self.db_app.query(ModelInfoDB)
                    .filter(ModelInfoDB.name.ilike(f"%{model_name}%"))
                    .all()
                )
                for model_info in model_infos:
                    ids.append(model_info.id)
                query = query.filter(ValidationMetricDB.model_id.in_(ids))

            result = query.all()

            if not result:
                log.error("No results found for the given filters.")
                raise NoResultFound("No results found for the given filters.")
            validation_info = [
                ValidationMetric.from_orm(validation_metric)
                for validation_metric in result
            ]
            log.info("Validation metrics details Information : %s", validation_info)
            return validation_info
        except NoResultFound as exc:
            log.error(
                " NoResultFound found while fetching Validation Metrics for "
                "the given details model id %s model_name %s %s ",
                model_pk,
                model_name,
                str(exc),
                exc_info=True,
            )
            raise NoResultFound(f"{str(exc)}")
        except Exception as exc:
            log.error(
                " Exception occurred while fetching Validation Metrics for "
                "the given details model id %s model_name %s %s ",
                model_pk,
                model_name,
                str(exc),
                exc_info=True,
            )
            raise OperationException(f"Unexpected error: {str(exc)}")

    def get_artifacts_details(
        self, model_pk=None, model_name=None
    ) -> List[ValidationArtifact]:
        """
        Retrieve validation artifacts details based on provided filters.

        Args:
            model_pk (int, optional): The ID of the model to retrieve. Defaults to None.
            model_name (str, optional): The name of the model to retrieve. Defaults to None.

        Returns:
            List[ValidationMetric]: The list of validation artifacts matching the filters.

        Raises:
            OperationException: If there is an unexpected error.
        """
        try:
            query = self.db_app.query(ValidationArtifactDB)
            ids: List[int] = [0]
            if model_pk:
                query = query.filter(ValidationArtifactDB.model_id == model_pk)
            if model_name:
                model_infos: List[ModelInfoDB] = (
                    self.db_app.query(ModelInfoDB)
                    .filter(ModelInfoDB.name.ilike(f"%{model_name}%"))
                    .all()
                )
                for model_info in model_infos:
                    ids.append(model_info.id)
                query = query.filter(ValidationArtifactDB.model_id.in_(ids))

            result = query.all()

            if not result:
                log.error("No results found for the given filters.")
                raise NoResultFound("No results found for the given filters.")
            validation_artifact = [
                ValidationArtifact.from_orm(validation_artifact)
                for validation_artifact in result
            ]
            log.info("validation artifacts: %s", validation_artifact)

            return validation_artifact
        except NoResultFound as exc:
            log.error(
                " NoResultFound found while fetching Validation Metrics for "
                "the given details model id %s model_name %s %s ",
                model_pk,
                model_name,
                str(exc),
                exc_info=True,
            )
            raise NoResultFound(f"{str(exc)}")
        except Exception as exc:
            log.error(
                " Exception occurred while fetching Validation Metrics for "
                "the given details model id %s model_name %s %s ",
                model_pk,
                model_name,
                str(exc),
                exc_info=True,
            )
            raise OperationException(f"Unexpected error: {str(exc)}")

    def upload_metrics_details(
        self, data: ValidationMetricInput
    ) -> List[ValidationMetric]:
        """
            upload validation metric details.
        :param data: data containing the validation metrics details
        :return: ValidationMetric : Data inserted to the DB
        """
        data_dict = data.dict()
        model_name = data_dict[constants.MODEL_NAME]
        if not model_name:
            raise ValidationException("Model name cannot be empty")
        accuracy_score = data_dict[constants.ACCURACY_SCORE]
        example_count = data_dict[constants.EXAMPLE_COUNT]
        f1_score = data_dict[constants.F1_SCORE]
        log_loss = data_dict[constants.LOG_LOSS]
        precision_score = data_dict[constants.PRECISION_SCORE]
        recall_score = data_dict[constants.RECALL_SCORE]
        roc_auc = data_dict[constants.ROC_AUC]
        score = data_dict[constants.SCORE]
        cpu_consumption = data_dict[constants.CPU_CONSUMPTION]
        memory_utilization = data_dict[constants.MEMORY_UTILIZATION]

        if not any(
            [
                accuracy_score,
                example_count,
                f1_score,
                log_loss,
                precision_score,
                recall_score,
                roc_auc,
                score,
                cpu_consumption,
                memory_utilization,
            ]
        ):
            log.error("At least one metric must be provided")
            raise ValidationException("At least one metric must be provided")
        try:
            model_infos: List[ModelInfoDB] = (
                self.db_app.query(ModelInfoDB)
                .filter(ModelInfoDB.name.ilike(f"%{model_name}%"))
                .all()
            )
            if not model_infos:
                log.error("Model %s is not found", model_name)
                raise NoResultFound(f"Model {model_name} is not found")
            modelids = [model_info.id for model_info in model_infos]

            model_datasets = (
                self.db_app.query(ModelDatasetDB)
                .filter(ModelDatasetDB.model_id.in_(modelids))
                .all()
            )

            validation_metric_infos = []
            for model_id in modelids:
                if model_datasets is None or len(model_datasets) == 0:
                    validation_metric_info = ValidationMetricDB(
                        model_id=model_id,
                        dataset_id=None,
                        accuracy_score=accuracy_score,
                        example_count=example_count,
                        f1_score=f1_score,
                        log_loss=log_loss,
                        precision_score=precision_score,
                        recall_score=recall_score,
                        roc_auc=roc_auc,
                        score=score,
                        cpu_consumption=cpu_consumption,
                        memory_utilization=memory_utilization,
                    )
                    self.db_app.add(validation_metric_info)
                    validation_metric_infos.append(validation_metric_info)
                else:
                    for model_dataset in model_datasets:
                        validation_metric_info = ValidationMetricDB(
                            model_id=model_id,
                            dataset_id=model_dataset.dataset_id,
                            accuracy_score=accuracy_score,
                            example_count=example_count,
                            f1_score=f1_score,
                            log_loss=log_loss,
                            precision_score=precision_score,
                            recall_score=recall_score,
                            roc_auc=roc_auc,
                            score=score,
                            cpu_consumption=cpu_consumption,
                            memory_utilization=memory_utilization,
                        )
                        self.db_app.add(validation_metric_info)
                        validation_metric_infos.append(validation_metric_info)
            self.db_app.commit()
            validation_metric_result = [
                ValidationMetric.from_orm(validation_metric)
                for validation_metric in validation_metric_infos
            ]
            log.info(
                "Created validation metrics successfully: %s", validation_metric_result
            )
            return validation_metric_result

        except IntegrityError as exc:
            log.error(
                "IntegrityError while saving Validation Metrics %s ",
                str(exc),
                exc_info=True,
            )
            self.db_app.rollback()
            log.error("Database error: %s", str(exc))
            raise OperationException(f"Database error: {str(exc)}")
        except Exception as exc:
            log.error(
                "Exception in saving Validation Metrics %s",
                str(exc),
                exc_info=True,
            )
            raise OperationException(f"Unexpected error: {str(exc)}")

    def save_validation_artifact(
        self, data: ValidationArtifactInput
    ) -> List[ValidationArtifact]:
        """
            save validation artifacts data in DB
        :param data: Validation artifacts data
        :return: ValidationArtifact : Details saved to the DB
        """
        data_dict = data.dict()
        model_name = data_dict["model_name"]
        if not model_name:
            log.error("Model name cant be empty: %s", model_name)
            raise ValidationException("Model name cannot be empty")
        try:
            model_infos: List[ModelInfoDB] = (
                self.db_app.query(ModelInfoDB)
                .filter(ModelInfoDB.name.ilike(f"%{model_name}%"))
                .all()
            )
            if not model_infos:
                log.error(
                    "No Model Found for saving Validation artifact: %s", model_name
                )
                raise NoResultFound(f"Model {model_name} is not found")
            modelids = [model_info.id for model_info in model_infos]

            model_datasets = (
                self.db_app.query(ModelDatasetDB)
                .filter(ModelDatasetDB.model_id.in_(modelids))
                .all()
            )

            validation_artifacts_infos = []
            for model_id in modelids:
                if model_datasets is None or len(model_datasets) == 0:
                    validation_artifact_info = ValidationArtifactDB(
                        model_id=model_id,
                        dataset_id=None,
                        validation_artifacts=data_dict["validation_artifacts"],
                    )
                    self.db_app.add(validation_artifact_info)
                    validation_artifacts_infos.append(validation_artifact_info)
                else:
                    for model_dataset in model_datasets:
                        validation_artifact_info = ValidationArtifactDB(
                            model_id=model_id,
                            dataset_id=model_dataset.dataset_id,
                            validation_artifacts=data_dict["validation_artifacts"],
                        )
                        self.db_app.add(validation_artifact_info)
                        validation_artifacts_infos.append(validation_artifact_info)
            self.db_app.commit()
            validation_artifact_result = [
                ValidationArtifact.from_orm(validation_artifact)
                for validation_artifact in validation_artifacts_infos
            ]
            log.info(
                "Created validation artifact successfully: %s",
                validation_artifact_result,
            )
            return validation_artifact_result

        except IntegrityError as exc:
            log.error(
                "IntegrityError while saving Validation Artifacts %s",
                str(exc),
                exc_info=True,
            )
            self.db_app.rollback()
            log.error("Database error: %s", str(exc))
            raise OperationException(f"Database error: {str(exc)}")
        except Exception as exc:
            log.error(
                "Exception in saving Validation Artifacts %s",
                str(exc),
                exc_info=True,
            )
            raise OperationException(f"Unexpected error: {str(exc)}")
