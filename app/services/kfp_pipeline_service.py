"""
    Module for Kfp Pipelines Service layer implementation
"""

import importlib

import os
from typing import List

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, NoResultFound

from app.middleware.logger import logger
from app.models.kfp_experiments import Experiment as ExperimentDB
from app.models.kfp_pipeline import Pipeline as PipelineDB
from app.models.kfp_run_details import RunDetails as RunDetailsDB
from app.models.kfp_tasks_info import Task as TaskDB

from app.schemas.kfp_details import KfpPipelineRunDetails, KfpPipelineRunDetailsInput
from app.schemas.kfp_experiments import Experiment
from app.schemas.kfp_pipeline import Pipeline
from app.schemas.kfp_run_details import RunDetails
from app.schemas.kfp_tasks_info import Task
from app.utils.exceptions import OperationException
from config import constants as const

log = logger()


class KfpPipelineService:
    """
    class for Kfp Pipeline  service layer implementation
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

    def upload_pipeline_details(
        self, data: KfpPipelineRunDetailsInput
    ) -> KfpPipelineRunDetails:
        """
        upload pipeline details.
        Args:
            data : details of the pipleine to save
        Returns:
            dict: saved pipeline details .
                otherwise a exception
        """
        try:
            data_dict = data.dict()
            pipeline_details = data_dict.get("pipeline_details", {})
            experiment_details = data_dict.get("experiment_details", {})
            run_details = data_dict.get("run_details", {})
            task_details = data_dict.get("task_details", {})
            model_id_details = data_dict.get("model_ids", {})

            kfp_experiment_info = ExperimentDB(
                uuid=experiment_details.get("uuid"),
                name=experiment_details.get("name"),
                description=experiment_details.get("description"),
                createdatinSec=experiment_details.get("createdatinSec"),
            )
            self.db_app.add(kfp_experiment_info)
            kfp_pipeline_infos = []
            if not model_id_details:
                kfp_pipeline_info = PipelineDB(
                    uuid=pipeline_details.get("uuid"),
                    # model_id=model_id,  # Set to None or replace with actual
                    # logic if model_id is available elsewhere
                    createdAt_in_sec=pipeline_details.get("createdAt_in_sec"),
                    name=pipeline_details.get("name"),
                    description=pipeline_details.get("description"),
                    parameters=pipeline_details.get("parameters"),
                    status=pipeline_details.get("status"),
                    pipeline_spec=pipeline_details.get("pipeline_spec"),
                    pipeline_spec_uri=pipeline_details.get("pipeline_spec_uri"),
                    experiment_uuid=experiment_details.get("uuid"),
                )
                self.db_app.add(kfp_pipeline_info)
                kfp_pipeline_infos.append(kfp_pipeline_info)
            else:
                for model_id in model_id_details:
                    kfp_pipeline_info = PipelineDB(
                        uuid=pipeline_details.get("uuid"),
                        model_id=model_id,  # Set to None or replace with actual
                        # logic if model_id is available elsewhere
                        createdAt_in_sec=pipeline_details.get("createdAt_in_sec"),
                        name=pipeline_details.get("name"),
                        description=pipeline_details.get("description"),
                        parameters=pipeline_details.get("parameters"),
                        status=pipeline_details.get("status"),
                        pipeline_spec=pipeline_details.get("pipeline_spec"),
                        pipeline_spec_uri=pipeline_details.get("pipeline_spec_uri"),
                        experiment_uuid=experiment_details.get("uuid"),
                    )
                    self.db_app.add(kfp_pipeline_info)
                    kfp_pipeline_infos.append(kfp_pipeline_info)

            kfp_run_info = RunDetailsDB(
                uuid=run_details.get("uuid"),
                name=run_details.get("name"),
                display_name=run_details.get("name"),
                description=run_details.get("description"),
                experiment_uuid=run_details.get("experiment_uuid"),
                pipeline_uuid=run_details.get("pipeline_uuid"),
                createdAt_in_sec=run_details.get("createdAt_in_sec"),
                scheduledAt_in_sec=run_details.get("scheduledAt_in_sec"),
                finishedAt_in_sec=run_details.get("finishedAt_in_sec"),
                state=run_details.get("state"),
            )

            self.db_app.add(kfp_run_info)
            kfp_task_infos = []
            for task_detail in task_details:
                kfp_task_info = TaskDB(
                    uuid=task_detail.get("uuid"),
                    name=task_detail.get("name"),
                    state=task_detail.get("state"),
                    runuuid=task_detail.get("runuuid"),
                    startedtimestamp=task_detail.get("startedtimestamp"),
                    finishedtimestamp=task_detail.get("finishedtimestamp"),
                    createdtimestamp=task_detail.get("createdtimestamp"),
                    parenttaskuuid=None,  # Update if you have logic for parent tasks
                )
                self.db_app.add(kfp_task_info)
                kfp_task_infos.append(kfp_task_info)

            # Commit the changes to the database
            self.db_app.commit()
            experiment_result = Experiment.from_orm(kfp_experiment_info)
            run_result = RunDetails.from_orm(kfp_run_info)
            pipeline_result = [
                Pipeline.from_orm(pipeline_info) for pipeline_info in kfp_pipeline_infos
            ]
            task_result = [Task.from_orm(task) for task in kfp_task_infos]

            return KfpPipelineRunDetails(
                run_details=run_result,
                experiment_details=experiment_result,
                pipeline_details=pipeline_result,
                task_details=task_result,
            )
        except IntegrityError as exc:
            self.db_app.rollback()
            log.error("Database error: %s", str(exc))
            raise OperationException(f"Database error: {str(exc)}")
        except Exception as exc:
            log.error("Unexpected error: %s", str(exc))
            raise OperationException(f"Unexpected error: {str(exc)}")

    def get_pipeline_by_model_id(self, model_id) -> List[Pipeline]:
        """
        Fetches pipeline information based on the provided model ID.
        Args:
            model_id (str): The ID of the model whose pipeline information is to be retrieved.
        Returns:
            dict: A dictionary containing either the pipeline details or an error message.
        """
        try:
            if not model_id:
                log.error("Model id missing")
                raise Exception("Model id missing")
            pipeline_info: List[PipelineDB] = (
                self.db_app.query(PipelineDB)
                .filter(PipelineDB.model_id == model_id)
                .all()
            )
            if len(pipeline_info) == 0:
                error_message = const.PIPELINE_MODEL_ID_ERROR_MSG
                log.error(error_message)
                raise Exception(error_message)
            log.info("Pipeline details Information : %s", pipeline_info)
            return [Pipeline.from_orm(pipeline) for pipeline in pipeline_info]
        except Exception as exp:
            log.error(
                " Exception occurred while fetching Pipeline for the given details model id %s %s ",
                model_id,
                str(exp),
                exc_info=True,
            )
            raise exp

    def list_runs_by_pipeline_id(self, pipeline_id: str) -> List[RunDetails]:
        """
        list runs by pipeline id
        Args:
        pipeline_id (int): ID of the pipeline.

        Returns:
        Response: List of Run details,
                  otherwise an exception.
        """
        try:
            if not pipeline_id:
                # return {"error": const.PIPELINE_ID_ERROR_MSG}
                raise Exception(const.PIPELINE_ID_ERROR_MSG)
            run_info: List[RunDetailsDB] = (
                self.db_app.query(RunDetailsDB)
                .filter(RunDetailsDB.pipeline_uuid == pipeline_id)
                .all()
            )

            if not run_info:
                error_message = const.RUN_NOT_FOUND
                log.error(
                    "%s for the given pipeline id %s ", error_message, pipeline_id
                )
            log.info("Run details Information : %s", run_info)
            return [RunDetails.from_orm(run) for run in run_info]
        except Exception as exp:
            error_message = const.RUN_EXCEPTION_MSG
            log.error(
                " %s %s %s ",
                error_message,
                pipeline_id,
                str(exp),
                exc_info=True,
            )
            raise exp

    def delete_runs_by_pipeline_id(self, pipeline_id: str) -> List[RunDetails]:
        """
        delete runs by pipeline id
        Args:
        pipeline_id (int): ID of the pipeline.

        Returns:
        Response: Deleted Run Details.
                  otherwise an exception.
        """
        try:
            if not pipeline_id:
                log.error(const.PIPELINE_ID_ERROR_MSG)
                raise Exception(const.PIPELINE_ID_ERROR_MSG)

            run_details: List[RunDetails] = []
            run_info = (
                self.db_app.query(RunDetailsDB)
                .filter(RunDetailsDB.pipeline_uuid == pipeline_id)
                .all()
            )
            if not run_info:
                error_message = const.RUN_NOT_FOUND
                log.error(" No Runs Found for the given pipeline id %s ", pipeline_id)
                raise NoResultFound(error_message)
            for run in run_info:
                self.db_app.delete(run)
                run_details.append(RunDetails.from_orm(run))
            self.db_app.commit()
            log.info(
                "Run details deleted successfully for the pipeline id %s", pipeline_id
            )
            return run_details

        except Exception as exp:
            error_message = const.RUN_DEL_EXCEPTION_MSG
            log.error(
                " Exception occurred while deleting Run Details for the given details pipeline id %s %s ",
                pipeline_id,
                str(exp),
                exc_info=True,
            )
            raise Exception(f"{error_message} : {str(exp)}")

    def delete_pipeline_details(self, pipeline_id) -> List[Pipeline]:
        """
        delete pipeline details by pipeline id
        Args:
        pipeline_id (int): ID of the pipeline.

        Returns:
        Response: deleted pipeline details.,
                  otherwise a exception.
        """
        try:
            if not pipeline_id:
                log.error(const.PIPELINE_ID_ERROR_MSG)
                raise Exception(const.PIPELINE_ID_ERROR_MSG)
            pipelines: List[Pipeline] = []
            pipeline_info: List[PipelineDB] = (
                self.db_app.query(PipelineDB)
                .filter(PipelineDB.uuid == pipeline_id)
                .all()
            )
            if not pipeline_info:
                error_message = const.PIPELINE_ID_ERROR_MSG
                log.error(
                    " No Pipeline Found for the given pipeline id %s ", pipeline_id
                )
                raise NoResultFound(error_message)

            for pipeline in pipeline_info:
                self.db_app.delete(pipeline)
                pipelines.append(Pipeline.from_orm(pipeline))
            self.db_app.commit()
            log.info("Pipeline deleted successfully : %s", pipeline_id)
            return pipelines
        except NoResultFound as exp:
            log.error(
                " Pipeline could not be found for the given pipeline id %s %s",
                pipeline_id,
                str(exp),
                exc_info=True,
            )
            error_message = const.PIPELINE_ID_ERROR_MSG
            raise Exception(error_message)
        except Exception as exp:
            error_message = const.PIPELINE_DEL_EXCEPTION_MSG
            log.error(
                " Exception occurred while deleting Pipeline for the given details pipeline id %s %s ",
                pipeline_id,
                str(exp),
                exc_info=True,
            )
            self.db_app.rollback()
            raise Exception(error_message)

    def check_pipeline_exists(self, pipeline_name) -> bool:
        """
            method to check if pipeline exists
        :param pipeline_name: name of the pipeline to check
        :return: True or False
        """
        pipeline_info: List[PipelineDB] = (
            self.db_app.query(PipelineDB).filter(PipelineDB.name == pipeline_name).all()
        )
        if not pipeline_info:
            return False
        return True
