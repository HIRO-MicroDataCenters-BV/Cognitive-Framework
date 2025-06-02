"""
Service for registering and retrieving model information.

This module provides a service class for registering new models and retrieving existing models from the database.
"""

import calendar
import importlib
import os
import shutil
from datetime import datetime, timedelta
from typing import List, Optional

import cogflow
import sqlalchemy.exc
from fastapi import UploadFile
from fastapi.responses import StreamingResponse
from minio import S3Error
from sqlalchemy import or_
from sqlalchemy.exc import (
    IntegrityError as DBIntegrityError,
    NoResultFound as NoRowFound,
)
from sqlalchemy.orm import Session

from app.middleware.logger import logger
from app.models.model_dataset import ModelDataset
from app.models.model_info import ModelInfo as ModelInfoDB
from app.models.model_upload import ModelFileUpload as ModelFileUploadDB
from app.schemas.dataset_info import DatasetInfoDetails
from app.schemas.model_dataset import ModelDetailedResponse
from app.schemas.model_info import (
    ModelInfoBase,
    ModelInfo,
    ModelDeploy,
    ModelUri,
    ModelInfoUpdate,
)
from app.schemas.model_upload import (
    ModelFileUpload as ModelFileUploadSchema,
    ModelFileUploadGet,
    ModelFileUploadPost,
    ModelFileUploadPut,
    ModelUploadUriPost,
    ModelFileUploadDetails,
)
from app.utils import cog_utils as util
from app.utils.exceptions import (
    OperationException,
    ModelNotFoundException,
    ModelFileExistsException,
    ModelFileNotFoundException,
    MinioClientError,
    NoResultFound,
    InvalidDurationException,
    IntegrityError,
)
from config import constants as const

log = logger()


class ModelRegisterService:
    """
    Service class for registering and retrieving model information.
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
        self.s3_client = util.S3Utils.create_s3_client()

    def register_model(self, data: ModelInfoBase) -> ModelInfo:
        """
        Register a new model in the database.

        Args:
            data (ModelInfoBase): The model information to register.

        Returns:
            ModelInfo: The registered model information.

        Raises:
            OperationException: If there is a database error or an unexpected error occurs.
        """
        try:
            data_dict = data.dict()
            model_info = ModelInfoDB(
                name=data_dict["name"],
                version=data_dict["version"],
                register_date=datetime.utcnow(),
                register_user_id=const.USER_ID,
                type=data_dict["type"],
                description=data_dict.get("description"),
                last_modified_time=datetime.utcnow(),
                last_modified_user_id=const.USER_ID,
            )
            # same model name and same version reject

            self.db_app.add(model_info)
            self.db_app.commit()
            result: ModelInfo = ModelInfo.from_orm(model_info)
            log.info("Created new model successfully %s", result)
            return result
        except DBIntegrityError as exc:
            self.db_app.rollback()
            raise OperationException(f"Database error: {str(exc)}")
        except Exception as exc:
            raise OperationException(f"Unexpected error: {str(exc)}")

    def get_model_details(
        self, last_days=None, model_pk=None, name=None
    ) -> List[ModelInfo]:
        """
        Retrieve model details based on provided filters.

        Args:
            last_days : duration of search
            model_pk (int, optional): The ID of the model to retrieve. Defaults to None.
            name (str, optional): The name of the model to retrieve. Defaults to None.

        Returns:
            List[ModelInfoSchema]: The list of models matching the filters.

        Raises:
            OperationException: If there is an unexpected error.
        """
        try:
            query = self.db_app.query(ModelInfoDB)
            current_year = datetime.now().year
            days_in_year = (
                const.LEAP_YEAR_DAYS
                if calendar.isleap(current_year)
                else const.NON_LEAP_YEAR_DAYS
            )
            if last_days is not None:
                if last_days > days_in_year:
                    raise InvalidDurationException(const.INVALID_DATE_RANGE_SELECT)
                threshold_date = datetime.utcnow() - timedelta(days=last_days)
                query = query.filter(
                    or_(
                        ModelInfoDB.register_date >= threshold_date,
                        ModelInfoDB.last_modified_time >= threshold_date,
                    )
                )
            if model_pk:
                query = query.filter(ModelInfoDB.id == model_pk)
            if name:
                query = query.filter(ModelInfoDB.name.ilike(f"%{name}%"))
            result = query.all()
            if not result:
                raise NoResultFound("No results found for the given filters.")
            model_info = [ModelInfo.from_orm(model) for model in result]
            log.info("Model Information List: %s", model_info)
            return model_info
        except NoResultFound as exc:
            log.error(
                "No result found for the given parameters: %s", str(exc), exc_info=True
            )
            raise NoResultFound(f"{str(exc)}")
        except Exception as exc:
            log.error(
                " Internal Exception occurred fetching model details %s",
                str(exc),
                exc_info=True,
            )
            raise OperationException(f"Unexpected error: {str(exc)}")

    def delete_model(self, model_id: int):
        """
        Delete a model by ID.

        Args:
            model_id (int): The ID of the model to delete.

        Returns:
            ModelInfo: The deleted model information.

        Raises:
            NoResultFound: If the model with the given ID is not found.
        """

        try:
            model = (
                self.db_app.query(ModelInfoDB).filter(ModelInfoDB.id == model_id).one()
            )
            if not model:
                raise NoResultFound(f"Model with ID {model_id} not found.")
            self.db_app.delete(model)
            self.db_app.commit()

            log.info(" Model id %s de-registered successfully. ", model_id)
        except sqlalchemy.exc.NoResultFound as exp:
            log.error(
                " Model could not be found for the given model id %s %s",
                model_id,
                str(exp),
                exc_info=True,
            )
            raise NoResultFound(f"Model with ID {model_id} not found.")
        except Exception as exp:
            log.error(
                " Internal Exception occurred during de-registering model %s",
                str(exp),
                exc_info=True,
            )
            raise exp

    def update_model(self, model_id: int, data: ModelInfoUpdate) -> ModelInfo:
        """
         Update a model by ID.

         Args:
             model_id (int): The ID of the model to update.
             data (ModelInfoBase): The updated model information.

         Returns:
             ModelInfo: The updated model information.

         Raises:
             NoResultFound: If the model with the given ID is not found.
        `"""
        try:
            model = (
                self.db_app.query(ModelInfoDB).filter(ModelInfoDB.id == model_id).one()
            )
            if not model:
                raise NoResultFound(f"Model with ID {model_id} not found.")

            # Get the data dictionary excluding unset values
            data_dict = data.dict(exclude_unset=True)

            # Check if there are any fields to update
            if not data_dict:
                log.info("No fields to update for model ID %s", model_id)
                result: ModelInfo = ModelInfo.from_orm(model)
                return result

            # Update the model with the provided data
            for key, value in data_dict.items():
                setattr(model, key, value)
            self.db_app.commit()
            self.db_app.refresh(model)
            updated_result: ModelInfo = ModelInfo.from_orm(model)
            log.info("Model Information updated successfully: %s", updated_result)
            return updated_result
        except sqlalchemy.exc.NoResultFound as exp:
            log.error(
                " Model could not be found for the given details model id %s %s ",
                model_id,
                str(exp),
                exc_info=True,
            )
            raise NoResultFound(f"Model with ID {model_id} not found.")
        except Exception as exp:
            log.error(
                " Exception occurred during model update for the model id %s %s ",
                model_id,
                str(exp),
                exc_info=True,
            )
            raise exp

    def upload_model_file(
        self, data: ModelFileUploadPost, file: UploadFile
    ) -> ModelFileUploadSchema:
        """
        Upload a new model file in the database.

        Args:
            data (ModelFileUploadPost): The model file information to upload.
            file (UploadFile): The file to upload.

        Returns:
            modelFileUploadSchema: The registered model file information.

        Raises:
            OperationException: If there is a database error or an unexpected error occurs.
            FileNotFoundError: File not found exception
            MinioClientError: Minioclienterror while connecting to the Minio
            Exception: Internal Exception
        """
        try:
            # Read the file content
            file_content = file.file.read()
            file_name = file.filename
            if not file_content:
                log.error("Missing Model File to upload.")
                raise FileNotFoundError("Missing Model File to upload.")
            model_upload_info = ModelFileUploadDB(
                model_id=data.model_id,
                user_id=const.USER_ID,  # Fix: be replaced with user service module
                register_date=datetime.utcnow(),
                file_name=file_name,
                file_path=f"{const.MINIO_CLIENT_NAME}://{const.BUCKET_NAME}",
                file_type=data.file_type,
                file_description=data.file_description,
            )
            if cogflow.save_to_minio(file_content, file_name, const.BUCKET_NAME):
                # Save the model file upload info to the database
                model_upload_info = self.save_model_file_upload(model_upload_info)
                result: ModelFileUploadSchema = ModelFileUploadSchema.from_orm(
                    model_upload_info
                )
                return result
            log.error("Failed to save the file to Minio.")
            raise MinioClientError("Failed to save the file to Minio.")

        except NoRowFound as exp:
            self.db_app.rollback()
            log.error(
                "No Model Id to upload%s",
                str(exp),
                exc_info=True,
            )
            raise NoResultFound("No Model Id Found")

        except FileNotFoundError as exp:
            self.db_app.rollback()
            log.error("FileNotFoundError exception %s", str(exp), exc_info=True)
            raise exp

        except S3Error as exp:
            self.db_app.rollback()
            log.error(
                "Exception occurred while connecting to Minio %s",
                str(exp),
                exc_info=True,
            )
            raise MinioClientError(str(exp))
        except OperationException as exp:
            self.db_app.rollback()
            log.error(
                "Operation exception occurred during uploading model file %s",
                str(exp),
                exc_info=True,
            )
            raise exp

        except Exception as exp:
            log.error(
                "Internal exception occurred during uploading model file %s",
                str(exp),
                exc_info=True,
            )
            raise exp

    def update_model_file(
        self, data: ModelFileUploadPut, file: UploadFile
    ) -> ModelFileUploadSchema:
        """
        Update model file in the database.

        Args:
            data (ModelFileUploadPut): The model file information to update.
            file (UploadFile): The file to update.

        Returns:
            ModelFileUploadSchema: The updated model file information.

        Raises:
            OperationException: If there is a database error or an unexpected error occurs.
            FileNotFoundError: File not found exception
            MinioClientError: Minioclienterror while connecting to the Minio
            Exception: Internal Exception
        """
        try:
            file_content = file.file.read()
            file_name = file.filename
            file_id = data.id
            if file_content:
                model_upload_infos = (
                    self.db_app.query(ModelFileUploadDB)
                    .filter(
                        ModelFileUploadDB.model_id
                        == data.model_id
                        # ModelFileUploadDB.user_id == data.user_id, # Fix: be replaced with user service module
                    )
                    .all()
                )
                if not model_upload_infos:
                    raise ModelNotFoundException("Model Id Not Found.")

                file_ids = {model_upload.id for model_upload in model_upload_infos}

                if file_id not in file_ids:
                    raise ModelFileNotFoundException("File ID not found.")

                for model_upload in model_upload_infos:
                    if (
                        model_upload.file_name != file_name
                        and model_upload.id == file_id
                    ):
                        model_upload.file_name = file_name
                        model_upload.file_description = data.file_description
                        if cogflow.save_to_minio(
                            file_content, file_name, const.BUCKET_NAME
                        ):
                            model_info = (
                                self.db_app.query(ModelInfoDB)
                                .filter(ModelInfoDB.id == model_upload.model_id)
                                .one()
                            )
                            model_info.last_modified_time = datetime.utcnow()
                            model_info.last_modified_user_id = (
                                const.USER_ID
                            )  # Fix: be replaced with user service module

                            self.db_app.commit()
                            result = ModelFileUploadSchema.from_orm(model_upload)
                            log.info("Updated Model File successfully %s", result)
                            return result
                log.info("Model File already exists.")
                raise ModelFileExistsException("Model File already exists.")
            log.info("Model File Update failed.")
            raise Exception("Model File Update failed.")

        except S3Error as exp:
            log.error(
                "Exception occurred while connecting to Minio %s",
                str(exp),
                exc_info=True,
            )
            raise MinioClientError(str(exp))

        except FileNotFoundError as exp:
            self.db_app.rollback()
            log.error(
                "File operation or Model file save operation failed %s",
                str(exp),
                exc_info=True,
            )
            raise exp

    def get_model_file_details(self, data: ModelFileUploadGet) -> ModelFileUploadSchema:
        """
        Get model file from the database.

        Args:
            data (ModelFileUploadGet): The model file information to update.

        Returns:
            modelFileUploadSchema: The searched model file information.

        Raises:
            ModelNotFoundException: Model Not Found
            OperationException: If there is a database error or an unexpected error occurs.
            Exception:
        """
        model_id = data.model_id
        file_name = data.file_name
        try:
            model_upload_infos = (
                self.db_app.query(ModelFileUploadDB)
                .filter(
                    ModelFileUploadDB.model_id
                    == model_id
                    # ModelFileUploadDB.user_id == user_id, # Fix: be replaced with user service module
                )
                .all()
            )

            for model_upload_info in model_upload_infos:
                if str(model_upload_info.file_name).rsplit(".", 1)[0] == file_name:
                    result: ModelFileUploadSchema = ModelFileUploadSchema.from_orm(
                        model_upload_info
                    )
                    log.info("Model File Upload Information : { %s }", result)
                    return result

            log.info("Model File Not Found for the given details.")
            raise ModelNotFoundException("Model File Not Found.")
        except Exception as exp:
            log.error(
                "Model File Upload Details Not Found for the model id %s %s",
                model_id,
                str(exp),
                exc_info=True,
            )

            raise exp

    def delete_model_file(self, file_id: int):
        """
        Delete model file details from db.

        Args:
            file_id (int): The ID of the model file to delete.

        Returns:
            str: The deletion status message.

        Raises:
            ModelNotFoundException: If the model file with the given ID is not found.
            OperationException: If there is a database error or an unexpected error occurs.
            Exception: If an unexpected error occurs.
        """
        try:
            model_upload_info = (
                self.db_app.query(ModelFileUploadDB)
                .filter(ModelFileUploadDB.id == file_id)
                .one()
            )
            if model_upload_info is not None:
                self.db_app.delete(model_upload_info)
                self.db_app.commit()
                log.info(" Model file id %s deleted successfully.", file_id)
                delete_status = cogflow.delete_from_minio(
                    model_upload_info.file_name, const.BUCKET_NAME
                )
                if delete_status:
                    return "Model file deleted successfully "
                raise MinioClientError("Minio Login Failed")
        except NoRowFound as exp:
            log.error(
                " Model file could not be found for this model file id. %s %s ",
                file_id,
                str(exp),
                exc_info=True,
            )
            raise NoResultFound
        except S3Error as exp:
            log.error(
                "Exception occurred while connecting to Minio %s",
                str(exp),
                exc_info=True,
            )
            raise MinioClientError(str(exp))
        except Exception as exp:
            log.error(
                "Internal Exception occurred while deleting the model file %s",
                str(exp),
                exc_info=True,
            )
            raise exp

    def save_model_file_upload(self, model_upload_info: ModelFileUploadDB):
        """
        Save model file upload information to the database.

        Args:
            model_upload_info (ModelFileUploadDB): The model file upload information.

        Returns:
            ModelFileUploadDB: The saved model file upload information.
        """
        try:
            # save details to DB
            self.db_app.add(model_upload_info)
            self.db_app.commit()
            model_info = (
                self.db_app.query(ModelInfoDB)
                .filter(ModelInfoDB.id == model_upload_info.model_id)
                .one()
            )
            model_info.last_modified_time = datetime.utcnow()
            model_info.last_modified_user_id = (
                const.USER_ID
            )  # Fix: be replaced with user service module

            self.db_app.commit()
            model_upload_detail = ModelFileUploadSchema.from_orm(model_upload_info)
            return model_upload_detail
        except NoRowFound as exp:
            log.error("No Result found for the given uri: %s", str(exp), exc_info=True)
            raise NoResultFound
        except Exception as exc:
            raise OperationException(f"Unexpected error: {str(exc)}")

    def download_model_file(
        self, model_id: Optional[int] = None, model_name: Optional[str] = None
    ) -> StreamingResponse:
        """
        Download model file from MinIO using model ID, model name, or both.

        Args:
            model_id (Optional[int]): ID of the model file to be downloaded.
            model_name (Optional[str]): Name of the model file to be downloaded.

        Returns:
            StreamingResponse: A streaming response containing the file.
        """
        try:
            model_zip_details = self.fetch_model_file_details(model_id, model_name)
            zip_files = self.fetch_file_details(model_zip_details)

            if not zip_files or not util.S3Utils.check_zip(zip_files):
                raise NoResultFound("No files available to zip.")

            model_id_or_name = str(model_id) if model_id else model_name
            return util.S3Utils.create_zip_file_from_s3(
                self.s3_client, zip_files, model_id_or_name
            )

        except NoRowFound as exp:
            log.error(
                "No result found for the given parameters: %s", str(exp), exc_info=True
            )
            raise NoResultFound

        except S3Error as exp:
            log.error(
                "Exception occurred during connecting to MinIO: %s",
                str(exp),
                exc_info=True,
            )
            raise MinioClientError(str(exp))

        except Exception as exp:
            log.error(
                "Exception occurred while retrieving model files: %s",
                str(exp),
                exc_info=True,
            )
            raise exp

    def fetch_model_file_details(
        self, model_id: Optional[int] = None, model_name: Optional[str] = None
    ) -> List[ModelFileUploadDB]:
        """
        Helper function to retrieve model file details based on model_id, model_name, or both.

        Args:
            model_id (Optional[int]): The ID of the model.
            model_name (Optional[str]): The name of the model.

        Returns:
            List[ModelFileUploadDB]: A list of model file details.

        Raises:
            NoResultFound: If no files are found for the given model ID or name.
            ValueError: If neither model_id nor model_name is provided.
        """
        if model_id and model_name:
            model_file_details = (
                self.db_app.query(ModelFileUploadDB)
                .join(ModelInfoDB, ModelFileUploadDB.model_id == ModelInfoDB.id)
                .filter(ModelInfoDB.id == model_id)
                .filter(ModelInfoDB.name.ilike(f"%{model_name}%"))
                .all()
            )

            if not model_file_details:
                raise NoResultFound(
                    f"No files found for model ID: {model_id} and name: {model_name}"
                )

            return model_file_details

        if model_id:
            model_file_details = (
                self.db_app.query(ModelFileUploadDB)
                .filter(ModelFileUploadDB.model_id == model_id)
                .all()
            )

            if not model_file_details:
                raise NoResultFound(f"No files found with ID: {model_id}")

            return model_file_details

        if model_name:
            return self.fetch_model_files_by_name(model_name)

        raise ValueError("Please provide either model_id or model_name to download.")

    def fetch_model_files_by_name(self, model_name: str) -> List[ModelFileUploadDB]:
        """
        Retrieve model files based on the model name.

        Args:
            model_name (str): The name of the model.

        Returns:
            List[ModelFileUploadDB]: A list of model file details.

        Raises:
            NoResultFound: If no models or files are found with the given name.
        """
        model_zip_details: List[ModelFileUploadDB] = []
        model_info = (
            self.db_app.query(ModelInfoDB)
            .filter(ModelInfoDB.name.ilike(f"%{model_name}%"))
            .all()
        )

        if not model_info:
            raise NoResultFound(f"No models found with the name: {model_name}")

        for model in model_info:
            model_files = (
                self.db_app.query(ModelFileUploadDB)
                .filter(ModelFileUploadDB.model_id == model.id)
                .all()
            )
            model_zip_details.extend(model_files)

        if not model_zip_details:
            raise NoResultFound(f"No files to zip for model name: {model_name}")

        return model_zip_details

    def register_model_uri(self, data: ModelUploadUriPost):
        """
        Register model by its uri.

        Args:
           data (ModelFileUpload): The model file information to register.

        Returns:
           ModelFileUpload: The registered model information.
        """
        try:
            if cogflow.is_valid_s3_uri(data.uri) is False:
                raise Exception("model-uri not valid")
            model_uri = data.uri.rstrip("/")
            uri_parts = model_uri.rsplit("/", 1)
            file_path = uri_parts[0]
            file_name = uri_parts[1]

            model_info = (
                self.db_app.query(ModelInfoDB)
                .filter(ModelInfoDB.id == data.model_id)
                .one()
            )
            model_upload_info = ModelFileUploadDB(
                model_id=data.model_id,
                user_id=const.USER_ID,  # Fix: be replaced with user service module
                register_date=datetime.utcnow(),
                file_path=file_path,
                file_name=file_name,
                file_type=data.file_type,  # model file type
                file_description=data.description,
            )
            self.db_app.add(model_upload_info)

            model_info.last_modified_time = datetime.utcnow()
            model_info.last_modified_user_id = (
                const.USER_ID
            )  # Fix: be replaced with user service module

            self.db_app.commit()
            model_upload_detail = ModelFileUploadSchema.from_orm(model_upload_info)
            log.info("Added Model Uri successfully %s", model_upload_detail)
            return model_upload_detail

        except DBIntegrityError as exp:
            log.error("Integrity error: %s", str(exp), exc_info=True)
            raise IntegrityError(message="Integrity error:", orig=exp)

        except NoRowFound as exp:
            log.error("No Results found: %s", str(exp), exc_info=True)
            raise NoResultFound
        except Exception as exp:
            log.error(
                "Exception occurred while saving model uri: %s", str(exp), exc_info=True
            )
            raise exp

    def fetch_model_uri(self, uri: str):
        """
        Retrieves the model ID associated with a given URI.
        Args:
            uri (str): The URI of the model. Expected to be in the format `s3://bucket-name/path/to/model`.
        Returns:
             str: The model ID associated with the given URI.
        """
        try:
            uri = uri.rstrip("/")
            uri_parts = uri.rsplit("/", 1)
            file_path = uri_parts[0]
            file_name = uri_parts[1]
            model_file_info = (
                self.db_app.query(ModelFileUploadDB)
                .filter(
                    ModelFileUploadDB.file_path == file_path,
                    ModelFileUploadDB.file_name == file_name,
                )
                .one()
            )

            return model_file_info.model_id
        except NoRowFound as exp:
            log.error("No Result found for the given uri: %s", str(exp), exc_info=True)
            raise NoResultFound
        except Exception as exp:
            log.error(
                "Exception occurred while fetching model uri details: %s",
                str(exp),
                exc_info=True,
            )
            raise exp

    def fetch_file_details(self, model_file_info: List[ModelFileUploadDB]):
        """
        fetch file details for contents to zip
        Args:
            model_file_info (List[ModelFileUploadDB]): List of ModelFileUploadDB details.
        Returns:
             list: contents of file_names to zip.
        """
        files_to_zip = []
        try:
            for model_file in model_file_info:
                model_path = model_file.file_path
                model_file_name = model_file.file_name
                bucket, key_prefix = util.S3Utils.split_s3_bucket_key_v2(
                    model_path + "/" + model_file_name
                )
                files_to_zip.append((bucket, key_prefix))
            return files_to_zip

        except Exception as exp:
            log.error(
                "Unable to fetch the contents to zip: %s", str(exp), exc_info=True
            )

    def log_model_in_cogflow(self, model_uri: ModelUri, files: UploadFile) -> ModelInfo:
        """
        1. call the logic in cogflow
        2. save model details in DB
        3. save model upload details in DB
        Args:
          :param model_uri: model info request data
          :param files: model file
        Returns:
        ModelFileUploadDB: The saved model file upload information.
        """
        try:
            file_content = files.file.read()
            file_name = files.filename
            if not os.path.exists(const.FILE_UPLOAD_PATH):
                os.makedirs(const.FILE_UPLOAD_PATH)
            if file_content and file_name:
                # log model in cogflow
                file_path = os.path.join(const.FILE_UPLOAD_PATH, file_name)
                with open(file_path, "wb") as buffer:
                    shutil.copyfileobj(files.file, buffer)
                log_model_result = cogflow.log_model_by_model_file(
                    os.path.join(const.FILE_UPLOAD_PATH, file_name), model_uri.name
                )
                os.remove(os.path.join(const.FILE_UPLOAD_PATH, file_name))

                # save model details in DB
                model_info = ModelInfoBase(
                    name=model_uri.name,
                    version=log_model_result.get("version"),
                    type=str(model_uri.file_type),
                    description=model_uri.description,
                )

                register_model_result = self.register_model(model_info)

                model_upload_info = ModelFileUploadDB(
                    model_id=register_model_result.id,
                    user_id=const.USER_ID,  # Fix: be replaced with user service module
                    register_date=datetime.utcnow(),
                    file_name=file_name,
                    file_path=log_model_result["artifact_uri"],
                    file_type=model_uri.file_type,
                    file_description=model_info.description,
                )

                # save model upload details in DB
                self.save_model_file_upload(model_upload_info)
                return register_model_result
            raise Exception("Model file not valid")
        except Exception as exp:
            log.error(
                "OperationError occurred during deleting the model file %s",
                str(exp),
                exc_info=True,
            )
            raise exp

    def deploy_model(self, data: ModelDeploy):
        """
        Deploy the model and create a inference service
        Args:
            data : ModelDeploy details to deploy model
        Returns:
        """
        try:
            msg = cogflow.deploy_model(
                model_name=data.name,
                model_version=data.version,
                isvc_name=data.isvc_name,
            )
            return msg
        except Exception as exp:
            log.error(
                "Exception occurred while deploy of model %s",
                str(exp),
                exc_info=True,
            )
            raise exp

    def undeploy_model(self, svc_name=None) -> str:
        """
        Deletes the served model with model_name
        Args:
            svc_name (str): model name
        Returns:
            str : Inference deletion message
        """
        try:
            if svc_name:
                response = cogflow.delete_served_model(svc_name)
                if response == "success":
                    return (
                        f"Inference Service {svc_name} has been deleted successfully."
                    )

                return f"Failed to delete Inference Service {svc_name}"

            return "Service name is required."
        except Exception as exp:
            log.error(
                "Exception occurred while deleting deployed service model %s",
                str(exp),
                exc_info=True,
            )
            raise exp

    def _process_model_infos(
        self, model_infos: List[ModelInfoDB]
    ) -> List[ModelDetailedResponse]:
        """
        Process model information and create detailed responses with datasets and files.

        Args:
            model_infos: List of ModelInfoDB objects to process.

        Returns:
            list: A list of ModelDetailedResponse objects.
        """
        results = []
        for model_info in model_infos:
            datasets = (
                self.db_app.query(ModelDataset).filter_by(model_id=model_info.id).all()
            )
            model_files = (
                self.db_app.query(ModelFileUploadDB)
                .filter_by(model_id=model_info.id)
                .all()
            )

            datasets_info = [entry.dataset_info for entry in datasets]
            data = ModelDetailedResponse(
                model_id=model_info.id,
                model_name=model_info.name,
                model_description=model_info.description,
                author=model_info.register_user_id,
                register_date=model_info.register_date.isoformat(),
                datasets=[
                    DatasetInfoDetails(
                        id=ds.id,
                        dataset_name=ds.dataset_name,
                        description=ds.description,
                        dataset_type=ds.train_and_inference_type,
                        data_source_type=ds.data_source_type,
                    )
                    for ds in datasets_info
                ],
                model_files=[
                    ModelFileUploadDetails(file_id=mf.id, file_name=mf.file_name)
                    for mf in model_files
                ],
            )
            results.append(data)

        return results

    def fetch_model_with_datasets(self, model_id: int):
        """
        Get model details along with datasets linked to it.
        Args:
            model_id (int): The ID of the model.

        Returns:
            list: A list of dictionaries containing model details with linked datasets and files.
        """
        try:
            query = self.db_app.query(ModelInfoDB)
            query = query.filter(ModelInfoDB.id == model_id)
            model_infos = query.all()
            if not model_infos:
                log.error("No Result found for the given model ID: %s", model_id)
                raise NoResultFound("No Result found for the given ID")

            return self._process_model_infos(model_infos)
        except Exception as exp:
            log.error(
                "Exception occurred while fetching model uri details: %s",
                str(exp),
                exc_info=True,
            )
            raise exp

    def fetch_model_with_datasets_by_name(self, model_name: str):
        """
        Get model details along with datasets linked to it, filtered by model name.
        Args:
            model_name (str): The name of the model (supports partial matching).

        Returns:
            list: A list of dictionaries containing model details with linked datasets and files.
        """
        try:
            query = self.db_app.query(ModelInfoDB)
            query = query.filter(ModelInfoDB.name.ilike(f"{model_name}%"))
            model_infos = query.all()
            if not model_infos:
                log.error("No Result found for the given model name: %s", model_name)
                raise NoResultFound("No Result found for the given name")

            return self._process_model_infos(model_infos)
        except Exception as exp:
            log.error(
                "Exception occurred while fetching model uri details: %s",
                str(exp),
                exc_info=True,
            )
            raise exp
