"""
Dataset Service implementation
"""

import calendar
import json
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

import cogflow
from fastapi import HTTPException, UploadFile
from kafka import KafkaConsumer
from sqlalchemy import func, create_engine
from sqlalchemy import or_
from sqlalchemy.engine import make_url
from sqlalchemy.exc import IntegrityError as DBIntegrityError
from sqlalchemy.exc import NoResultFound as NoRowFound
from sqlalchemy.exc import SQLAlchemyError, OperationalError
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.sql import select
from werkzeug.utils import secure_filename

from app.middleware.logger import logger
from app.models import (
    ModelInfo,
    ModelDataset,
    DatasetInfo,
    DatasetFileDetails,
    DatasetTableDetails,
    DatasetTopicDetails,
    BrokerDetails,
    TopicDetails,
)
from app.schemas.broker_details import BrokerBase, BrokerResponse, BrokerUpdate
from app.schemas.dataset_broker_topic import (
    DatasetBrokerTopicBase,
    DatasetBrokerTopicResponse,
    DatasetTopicData,
    BrokerTopicDetails,
)
from app.schemas.dataset_info import DatasetInfoDetails
from app.schemas.dataset_table_register import DatasetTable, DatasetTableRegister
from app.schemas.dataset_upload import (
    DatasetUploadBase,
    DatasetUpdateBase,
    DatasetUploadResponse,
)
from app.schemas.topic_details import TopicBase, TopicResponse, TopicUpdate
from app.utils import cog_utils as util
from app.utils.exceptions import (
    NoResultFound,
    IntegrityError,
    InvalidDurationException,
    DatasetTableExistsException,
    DatabaseException,
    OperationException,
    NoMessagesFound,
)
from config import constants as const

log = logger()


class DatasetService:
    """
    Dataset Service
    """

    def __init__(self, db_app: Session):
        """
        Initialize the DatasetService with a database session.

        Args:
            db_app (Session): The database session.
        """
        self.db_app = db_app

    async def upload_file(self, request: DatasetUploadBase, file: UploadFile):
        """
        Upload a dataset file to Minio and save its details to the database.

        Args:
            request (DatasetUploadBase): The dataset upload request data.
            file (UploadFile): The file to upload.

        Returns:
            DatasetUploadModel: The saved dataset upload details.

        Raises:
            Exception: If the dataset file is missing or an error occurs.
        """
        try:
            if file:
                if file.filename is None:
                    raise ValueError("file.filename cannot be None")
                file_data = await file.read()
                filename = secure_filename(file.filename)
                if cogflow.save_to_minio(file_data, filename, const.BUCKET_NAME):
                    return await self.add_dataset_details_to_db(request, filename)
            raise Exception("Dataset Not Found or Missing Dataset File.")
        except DBIntegrityError as exp:
            log.error(
                "Dataset already exists %s",
                str(exp),
                exc_info=True,
            )
            raise IntegrityError(
                message="A file with the same name already exists for this user.",
                orig=exp,
            )

        except Exception as exp:
            self.db_app.rollback()
            log.error(
                "Internal exception occurred while uploading dataset file  %s",
                str(exp),
                exc_info=True,
            )
            raise exp

    async def add_dataset_details_to_db(
        self, request: DatasetUploadBase, filename: str
    ):
        """
        Add dataset details to the database.

        Args:
            request (DatasetUploadBase): The dataset upload request data.
            filename (str): The name of the uploaded file.

        Returns:
            DatasetUploadModel: The saved dataset upload details.
        """
        datasets = DatasetInfo(
            user_id=const.USER_ID,
            register_date_time=datetime.utcnow(),
            last_modified_time=datetime.utcnow(),
            last_modified_user_id=const.USER_ID,
            dataset_name=request.dataset_name,
            description=request.description,
            train_and_inference_type=request.dataset_type,
            data_source_type=const.DATA_SOURCE_TYPE_FILE,
        )
        self.db_app.add(datasets)
        self.db_app.flush()
        dataset_file = DatasetFileDetails(
            dataset_id=datasets.id,
            user_id=const.USER_ID,
            register_date=datetime.utcnow(),
            file_path=f"{const.MINIO_CLIENT_NAME}://{const.BUCKET_NAME}",
            file_name=filename,
        )

        self.db_app.add(dataset_file)
        self.db_app.commit()
        result = DatasetUploadResponse(
            id=dataset_file.id,
            dataset_id=dataset_file.dataset_id,
            file_path=dataset_file.file_path,
            file_name=dataset_file.file_name,
            register_date=dataset_file.register_date,
            description=datasets.description,
            dataset_name=datasets.dataset_name,
            dataset_type=datasets.train_and_inference_type,
        )

        log.info("Created new dataset successfully %s", result)
        return result

    async def search_datasets(
        self, last_days: Optional[int], name: Optional[str], dataset_id: Optional[int]
    ):
        """
        Search for datasets based on filters.

        Args:
            last_days (Optional[int]): The number of days to look back.
            name (Optional[str]): The name of the dataset.
            dataset_id (Optional[int]): The primary key of the dataset.

        Returns:
            List[DatasetInfo]: The list of datasets matching the filters.

        Raises:
            NoResultFound: If no datasets are found.
            Exception: If an error occurs while searching datasets.
        """
        try:
            query = self.db_app.query(DatasetInfo)
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
                        DatasetInfo.register_date_time >= threshold_date,
                        DatasetInfo.last_modified_time >= threshold_date,
                    )
                )
            if name is not None:
                query = query.filter(DatasetInfo.dataset_name.ilike(f"%{name}%"))
            if dataset_id is not None:
                query = query.filter(DatasetInfo.id == dataset_id)

            results = query.all()
            if not results:
                raise NoResultFound("Datasets not found.")
            log.info("Dataset Details: %s", results)
            return results
        except NoResultFound as exp:
            log.error(
                "No Dataset Found for the given details %s",
                str(exp),
                exc_info=True,
            )
            raise NoResultFound(str(exp))
        except Exception as exp:
            log.error(
                "Internal exception occurred while searching datasets %s",
                str(exp),
                exc_info=True,
            )
            raise exp

    async def deregister_dataset(self, dataset_id: int):
        """
        Deregister a dataset by its primary key.

        Args:
            dataset_id (int): The primary key of the dataset.

        Returns:
            Tuple[bool, str]: A tuple indicating success and a message.

        Raises:
            Exception: If the dataset is not found or an error occurs.
        """
        try:
            mdi = (
                self.db_app.query(DatasetInfo)
                .filter(DatasetInfo.id == dataset_id)
                .one()
            )
            if mdi.data_source_type == const.DATA_SOURCE_TYPE_FILE:
                dataset_upload = (
                    self.db_app.query(DatasetFileDetails)
                    .filter(DatasetFileDetails.id == dataset_id)
                    .one()
                )
                cogflow.delete_from_minio(dataset_upload.file_name, const.BUCKET_NAME)
            self.db_app.delete(mdi)
            self.db_app.commit()
            log.info("Dataset deleted successfully")

        except NoRowFound as exp:
            log.error(
                "Dataset not found for the id %s %s",
                dataset_id,
                str(exp),
                exc_info=True,
            )
            raise NoResultFound(f"Dataset not found for the id {dataset_id}")
        except Exception as exp:
            log.error(
                "Internal exception occurred while de-registering dataset. %s",
                str(exp),
                exc_info=True,
            )
            raise exp

    async def link_dataset_model(self, dataset_id: int, model_id: int):
        """
        Link a dataset to a model.

        Args:
            dataset_id (int): The ID of the dataset.
            model_id (int): The ID of the model.

        Returns:
            dict: The linked dataset and model details.

        Raises:
            NoResultFound: If the dataset or model is not found.
            Exception: If the model is already linked to the dataset or an error occurs.
        """
        try:
            model_exists = (
                self.db_app.query(ModelInfo).filter(ModelInfo.id == model_id).scalar()
                is not None
            )
            if not model_exists:
                log.error("Model with id %s not found", model_id)
                raise NoResultFound(f"Model with id {model_id} not found")

            dataset_exists = (
                self.db_app.query(DatasetInfo)
                .filter(DatasetInfo.id == dataset_id)
                .scalar()
                is not None
            )
            if not dataset_exists:
                log.error("Dataset with id %s not found", dataset_id)
                raise NoResultFound(f"Dataset with id {dataset_id} not found")

            link_exists = (
                self.db_app.query(ModelDataset)
                .filter(
                    ModelDataset.model_id == model_id,
                    ModelDataset.dataset_id == dataset_id,
                )
                .scalar()
                is not None
            )
            if link_exists:
                log.error(
                    "Model with id %s is already linked to dataset with id %s",
                    model_id,
                    dataset_id,
                )
                raise HTTPException(
                    status_code=400,
                    detail=f"Model with id {model_id} is already linked to dataset with id {dataset_id}",
                )

            new_link = ModelDataset(
                model_id=model_id,
                dataset_id=dataset_id,
                linked_time=datetime.now(),
                user_id=const.USER_ID,
            )
            self.db_app.add(new_link)
            self.db_app.commit()

            saved_data = {
                "model_id": new_link.model_id,
                "dataset_id": new_link.dataset_id,
                "linked_time": new_link.linked_time.strftime("%Y-%m-%d %H:%M:%S"),
            }
            log.info("Model and dataset linked successfully %s ", saved_data)
            return saved_data
        except NoRowFound as exp:
            log.error(
                "No Result found for the given details. %s",
                str(exp),
                exc_info=True,
            )
            raise NoResultFound(str(exp))
        except SQLAlchemyError as exp:
            self.db_app.rollback()
            log.error(
                "Error occurred while linking dataset with model. %s",
                str(exp),
                exc_info=True,
            )
            raise exp
        except Exception as exp:
            self.db_app.rollback()
            log.error(
                "Internal Exception while linking dataset with model. %s",
                str(exp),
                exc_info=True,
            )
            raise exp

    async def unlink_dataset_model(self, dataset_id: int, model_id: int):
        """
        Unlink a dataset from a model.

        Args:
            dataset_id (int): The ID of the dataset.
            model_id (int): The ID of the model.

        Returns:
            dict: The unlinked dataset and model details.

        Raises:
            NoResultFound: If the link between the dataset and model is not found.
            Exception: If an error occurs while unlinking the dataset from the model.
        """
        try:
            link = (
                self.db_app.query(ModelDataset)
                .filter(
                    ModelDataset.model_id == model_id,
                    ModelDataset.dataset_id == dataset_id,
                )
                .one_or_none()
            )
            if not link:
                raise NoResultFound(
                    f"Link between model with id {model_id} and dataset with id {dataset_id} not found"
                )

            self.db_app.delete(link)
            self.db_app.commit()

            unlinked_data = {"model_id": model_id, "dataset_id": dataset_id}
            log.info("Model and Dataset unliked successfully %s", unlinked_data)
            return unlinked_data
        except NoResultFound as exp:
            log.error(
                "NoResultFound for the model id %s dataset id %s with %s",
                model_id,
                dataset_id,
                str(exp),
                exc_info=True,
            )
            raise NoResultFound(str(exp))
        except SQLAlchemyError as exp:
            log.error(
                "Error occurred while unlinking dataset from model %s",
                str(exp),
                exc_info=True,
            )
            self.db_app.rollback()
            raise exp

    async def register_dataset_table(self, data: DatasetTable):
        """
         implementation of dataset table registration

        Args:
            data (Model): The ID of the dataset.

        Returns:
            dict: The unlinked dataset and model details.

        Raises:
          DBIntegrityError : IntegrityError
          Exception : Internal Exception

        """
        try:
            dataset_info = DatasetInfo(
                train_and_inference_type=data.dataset_type,
                data_source_type=const.DATA_SOURCE_TYPE_TABLE,
                dataset_name=data.name,
                user_id=const.USER_ID,
                register_date_time=datetime.utcnow(),
                last_modified_time=datetime.utcnow(),
                last_modified_user_id=const.USER_ID,
                description=data.description,
            )
            self.db_app.add(dataset_info)
            self.db_app.flush()
            dataset_table = DatasetTableDetails(
                dataset_id=dataset_info.id,
                user_id=const.USER_ID,
                register_date=datetime.utcnow(),
                db_url=data.db_url,
                table_name=data.table_name,
                fields_selected_list=data.selected_fields,
            )
            self.db_app.add(dataset_table)
            self.db_app.commit()
            ds_table_register_result = DatasetTableRegister(
                id=dataset_table.id,
                dataset_id=dataset_table.dataset_id,
                dataset_name=dataset_info.dataset_name,
                description=dataset_info.description,
                dataset_type=dataset_info.train_and_inference_type,
                db_url=dataset_table.db_url,
                table_name=dataset_table.table_name,
                fields_selected_list=dataset_table.fields_selected_list,
                register_date=dataset_table.register_date,
            )

            log.info(
                " Dataset Table Register Details Added %s ", ds_table_register_result
            )

            self.db_app.flush()
            return ds_table_register_result
        except DBIntegrityError as exp:
            self.db_app.rollback()
            log.error("Dataset table Already Exists. %s", str(exp), exc_info=True)
            raise IntegrityError(message="Dataset table Already Exists.", orig=exp)
        except Exception as exp:
            self.db_app.rollback()
            log.error("Unable to save db details %s", str(exp), exc_info=True)
            raise exp

    def update_dataset_table(self, data: DatasetTable):
        """
        implementation for updating dataset_table
        Args:
           data (DatasetTableRegister): DatasetTableRegister details.
        Returns:
           DatasetTableRegister details
        Raises:
           NoResultFound : No Result found
           Exception : Internal Exception

        """
        try:
            dataset_table_register_info = (
                self.db_app.query(DatasetTableDetails)
                .filter(
                    DatasetTableDetails.user_id == const.USER_ID,
                    DatasetTableDetails.table_name == data.table_name,
                )
                .one()
            )
            if dataset_table_register_info.fields_selected_list == data.selected_fields:
                log.info("Dataset Table Register Details Already Exists ")
                raise DatasetTableExistsException(
                    "Dataset Table Register Details Already Exists"
                )
            dataset_info = (
                self.db_app.query(DatasetInfo)
                .filter(DatasetInfo.id == dataset_table_register_info.dataset_id)
                .one()
            )
            dataset_info.dataset_name = data.name
            dataset_info.description = data.description
            dataset_table_register_info.fields_selected_list = data.selected_fields
            self.db_app.commit()
            log.info(
                " Dataset table Register Details Updated %s",
                dataset_table_register_info,
            )
            ds_table_register_result = DatasetTableRegister(
                id=dataset_table_register_info.id,
                dataset_id=dataset_table_register_info.dataset_id,
                dataset_name=dataset_info.dataset_name,
                description=dataset_info.description,
                dataset_type=dataset_info.train_and_inference_type,
                db_url=dataset_table_register_info.db_url,
                table_name=dataset_table_register_info.table_name,
                fields_selected_list=dataset_table_register_info.fields_selected_list,
                register_date=dataset_table_register_info.register_date,
            )

            return ds_table_register_result
        except NoRowFound as exp:
            log.error("Dataset not registered. %s", str(exp), exc_info=True)
            raise NoResultFound

    def fetch_db_tables(self, request_url: str):
        """
        implementation for fetch db table details using db_url
        Args:
           request_url ( str) : database url
        Returns:

        Raises:
           OperationError : Operation Exception
           SQLAlchemyError : Database error
           Exception : Internal Exception

        """
        table_fields = {}
        final_columns = ""
        try:
            url = make_url(request_url)
            metadata = util.DBUtils.db_engine_create(url)
            tables = metadata.tables.keys()

            table_info = []

            for table_name in tables:
                # id - link with training model id or see for table name
                columns = metadata.tables[table_name].columns
                for column in columns:
                    table_fields[column.name] = column.type
                counter = self.db_app.query(
                    metadata.tables[table_name]
                ).statement.with_only_columns([func.count()])
                row_count = self.db_app.execute(counter).scalar()
                table_columns = str(table_fields)
                if table_columns.startswith("{") and table_columns.endswith("}"):
                    final_columns = table_columns[1:-1].replace("'", "")
                table_info.append(
                    {
                        "table_name": table_name,
                        "fields": final_columns,
                        "records_count": row_count,
                    }
                )
            log.info("Database details %s", table_info)
            result = {url.database: table_info}
            return result

        except OperationalError as exp:
            log.error(
                "OperationalError occurred while retrieving db details %s",
                str(exp),
                exc_info=True,
            )
            raise OperationException(str(exp))

        except SQLAlchemyError as exp:
            log.error("Unable to connect database %s", str(exp), exc_info=True)
            raise DatabaseException(str(exp))

        except Exception as exp:
            log.error(
                "Exception occurred while retrieving db details %s",
                str(exp),
                exc_info=True,
            )
            raise exp

    def register_broker(self, data: BrokerBase) -> BrokerResponse:
        """
        implementation to save broker details
         Args:
            data (BrokerBase) : Broker details to save
         Returns: BrokerResponse

         Raises:
             DBIntegrityError : Db Integrity error
             OperationalError: Operational error during retrieval
             SQLAlchemyError: SQLAlchemyError
             Exception : Unable to save broker details

        """
        try:
            broker_details = BrokerDetails(
                broker_name=data.name,
                broker_ip=data.ip,
                broker_port=data.port,
                creation_date=datetime.utcnow(),
            )
            self.db_app.add(broker_details)
            self.db_app.commit()
            broker_info = BrokerResponse.from_orm(broker_details)
            log.info("Broker details %s", broker_info)
            return broker_info
        except DBIntegrityError as exp:
            self.db_app.rollback()

            existing_broker = (
                self.db_app.query(BrokerDetails)
                .filter(BrokerDetails.broker_name == data.name)
                .one()
            )

            broker_id = existing_broker.id

            log.error(
                "Integrity error: Constraint violation or duplicate data. %s",
                str(exp),
                exc_info=True,
            )
            raise IntegrityError(
                message=f"Broker id {broker_id} already exists.", orig=exp
            )

        except SQLAlchemyError as exp:
            self.db_app.rollback()
            log.error(
                "Database error: Unable to save Broker details. %s",
                str(exp),
                exc_info=True,
            )
            raise exp
        except Exception as exp:
            self.db_app.rollback()
            log.error(
                "Operational error: Database connection failure. %s",
                str(exp),
                exc_info=True,
            )
            raise exp

    def fetch_file_details_for_dataset(self, dataset_id: int):
        """
        implementation to fetch dataset file details
        Args:
          dataset_id : dataset id
          Returns:

        Raises:
            NoRowFound : No Result Found
            Exception : Unable to retrieve dataset file details
        """
        try:
            dataset_info = (
                self.db_app.query(DatasetInfo)
                .filter(DatasetInfo.id == dataset_id)
                .one()
            )
            dataset_upload = (
                self.db_app.query(DatasetFileDetails)
                .filter(DatasetFileDetails.dataset_id == dataset_id)
                .one()
            )
            result = DatasetUploadResponse(
                id=dataset_upload.id,
                dataset_id=dataset_upload.dataset_id,
                register_date=dataset_upload.register_date,
                file_name=dataset_upload.file_name,
                file_path=dataset_upload.file_path,
                description=dataset_info.description,
                dataset_name=dataset_info.dataset_name,
                dataset_type=dataset_info.train_and_inference_type,
            )
            log.info(
                "Database file details for the dataset ID %s : %s", dataset_id, result
            )
            return result
        except NoRowFound as exp:
            log.error(
                "Dataset not found for given dataset ID %s : %s",
                dataset_id,
                str(exp),
                exc_info=True,
            )
            raise NoResultFound

        except Exception as exp:
            log.error(
                "Error fetching dataset file details for given dataset ID %s : %s",
                dataset_id,
                str(exp),
                exc_info=True,
            )
            raise exp

    def fetch_table_details_for_dataset(self, dataset_id: int):
        """
        implementation to fetch table details based on dataset_id
        Args:
          dataset_id : dataset id
        Returns: DatasetTableRegister details

        Raises:
            NoRowFound : No Result Found
            Exception : Unable to retrieve table details
        """
        try:
            dataset_info = (
                self.db_app.query(DatasetInfo)
                .filter(DatasetInfo.id == dataset_id)
                .one()
            )
            dataset_table = (
                self.db_app.query(DatasetTableDetails)
                .filter(DatasetTableDetails.dataset_id == dataset_id)
                .one()
            )

            result = DatasetTableRegister(
                id=dataset_table.id,
                dataset_id=dataset_table.dataset_id,
                dataset_name=dataset_info.dataset_name,
                description=dataset_info.description,
                dataset_type=dataset_info.train_and_inference_type,
                db_url=dataset_table.db_url,
                table_name=dataset_table.table_name,
                fields_selected_list=dataset_table.fields_selected_list,
                register_date=dataset_table.register_date,
            )
            return result

        except NoRowFound as exp:
            log.error("Dataset not found. %s", str(exp), exc_info=True)
            raise NoResultFound

        except Exception as exp:
            log.error(
                "Error fetching dataset table details: %s", str(exp), exc_info=True
            )
            raise exp

    def register_topic(self, broker_id: int, data: TopicBase) -> TopicResponse:
        """
        implementation to save topic details based on topic information
        Args:
           data: TopicBase
           broker_id : id of the broker
        Returns: TopicResponse details
        Raises:
           DBIntegrityError : Integrity error for duplicates
           Exception : Unable to save topic information
        """
        try:
            broker_info = (
                self.db_app.query(BrokerDetails)
                .filter(BrokerDetails.id == broker_id)
                .one_or_none()
            )
            if not broker_info:
                raise NoResultFound(f"Broker with name {broker_id} not found.")
            topic_details = TopicDetails(
                topic_name=data.name,
                topic_schema=data.schema_definition,
                broker_id=broker_id,
                creation_date=datetime.utcnow(),
            )

            self.db_app.add(topic_details)
            self.db_app.commit()
            topic_info = TopicResponse.from_orm(topic_details)
            log.info("Topic details %s", topic_info)
            return topic_info
        except DBIntegrityError as exp:
            self.db_app.rollback()
            log.error(
                "Integrity error: Constraint violation or duplicate data. %s",
                str(exp),
                exc_info=True,
            )

            existing_topic = (
                self.db_app.query(TopicDetails)
                .filter(TopicDetails.topic_name == data.name)
                .one()
            )

            topic_id = existing_topic.id

            raise IntegrityError(
                message=f"Topic id {topic_id} already exists.", orig=exp
            )
        except NoRowFound:
            raise NoResultFound(f"Broker Id {broker_id} not found.")
        except SQLAlchemyError as exp:
            self.db_app.rollback()
            log.error(
                "Database error: Unable to save Topic details. %s",
                str(exp),
                exc_info=True,
            )
            raise exp
        except Exception as exp:
            self.db_app.rollback()
            log.error("Unable to save Topic details %s", str(exp), exc_info=True)
            raise exp

    def fetch_broker_details(self) -> List[BrokerResponse]:
        """
            Fetches a list of broker details from the database.

        Returns:
            List[BrokerResponse]:
                A list of broker details represented as `BrokerResponse` objects.

        Raises:
            NoResultFound:
                Raised when no brokers are found in the database for the given query.
            OperationException:
                Raised for unexpected exceptions or errors during the operation.
        """
        try:
            query = self.db_app.query(BrokerDetails)
            result = query.all()
            if not result:
                log.error("No Broker defined.")
                raise NoResultFound("No Broker defined")
            broker_info = [BrokerResponse.from_orm(broker) for broker in result]
            log.info("Broker Information List: %s", broker_info)
            return broker_info

        except Exception as exp:
            log.error(
                " Internal Exception occurred fetching broker details %s",
                str(exp),
                exc_info=True,
            )
            raise exp

    def fetch_topic_details(self) -> List[TopicResponse]:
        """
        Fetches a list of topic details from the database.

        Returns:
            List[TopicResponse]:
                A list of topic details represented as `TopicResponse` objects.

        Raises:
            NoResultFound:
                Raised when no topics are found in the database for the given query.
            OperationException:
                Raised for unexpected exceptions or errors during the operation.
        """
        try:
            query = self.db_app.query(TopicDetails)
            result = query.all()
            if not result:
                log.error("No Topic defined.")
                raise NoResultFound("No topics defined")
            topic_info = [TopicResponse.from_orm(topic) for topic in result]
            log.info("Topic Information List: %s", topic_info)
            return topic_info

        except Exception as exp:
            log.error(
                " Internal Exception occurred fetching topic details %s",
                str(exp),
                exc_info=True,
            )
            raise exp

    def register_dataset_message_details(self, data: DatasetBrokerTopicBase):
        """
        Saves dataset, broker, and topic details to the database.

        Args:
            data (DatasetBrokerTopicBase):
                An object containing the dataset name, description, dataset type,
                broker information, and topic details.

        Returns:
            DatasetBrokerTopicResponse:
                A structured response containing details about the dataset, broker, and topic
                that were saved in the database.

        Raises:
            IntegrityError:
                Raised when there is a database constraint violation, such as duplicate data
                or missing foreign key relationships.
            OperationException:
                Raised when there is an operational issue with the database, such as connection
                problems.
            SQLAlchemyError:
                Raised when a generic SQLAlchemy-related database error occurs.
            Exception:
                Raised for any other general exceptions during the save process.

        """
        try:
            broker_info = (
                self.db_app.query(BrokerDetails)
                .filter(BrokerDetails.id == data.broker_id)
                .one_or_none()
            )
            if not broker_info:
                raise NoResultFound(f"Broker with name {data.broker_id} not found.")
            topic_info = (
                self.db_app.query(TopicDetails)
                .filter(TopicDetails.id == data.topic_id)
                .one_or_none()
            )
            if not topic_info:
                raise NoResultFound(f"Topic with name {data.topic_id} not found.")

            # to handle duplicate entries
            dataset_info = DatasetInfo(
                user_id=const.USER_ID,  # to be defined with user service
                register_date_time=datetime.utcnow(),
                last_modified_time=datetime.utcnow(),
                last_modified_user_id=const.USER_ID,  # to be defined with user service
                dataset_name=data.name,
                description=data.description,
                train_and_inference_type=data.dataset_type,
                data_source_type=const.BROKER_DATA_SOURCE_TYPE,
            )
            self.db_app.add(dataset_info)
            self.db_app.flush()
            dataset_topic_info = DatasetTopicDetails(
                topic_id=data.topic_id,
                dataset_id=dataset_info.id,
                creation_date=datetime.utcnow(),
            )
            self.db_app.add(dataset_topic_info)
            self.db_app.commit()
            dataset_detail = DatasetInfoDetails(
                id=dataset_info.id,
                dataset_name=dataset_info.dataset_name,
                description=dataset_info.description,
                dataset_type=dataset_info.train_and_inference_type,
                data_source_type=dataset_info.data_source_type,
            )
            broker_detail = BrokerResponse.from_orm(broker_info)
            topic_detail = TopicResponse.from_orm(topic_info)
            response = self.dataset_message_response(
                dataset_detail, broker_detail, topic_detail
            )

            log.info("Messaging components register details %s", response)
            return response
        except DBIntegrityError as exp:
            self.db_app.rollback()
            log.error(
                "Integrity error: Constraint violation or duplicate data. %s",
                str(exp),
                exc_info=True,
            )
            raise IntegrityError(message="Broker already Exists.", orig=exp)
        except SQLAlchemyError as exp:
            self.db_app.rollback()
            log.error(
                "Database error: Unable to save Broker details. %s",
                str(exp),
                exc_info=True,
            )
            raise exp
        except Exception as exp:
            self.db_app.rollback()
            log.error("Unable to save Broker details %s", str(exp), exc_info=True)
            raise exp

    def fetch_dataset_message_details(self, dataset_id: int):
        """
        Retrieve detailed information about a dataset, its associated broker, and topic details.

        Args:
            dataset_id (int): The unique identifier of the dataset for which details are requested.

        Returns:
            Tuple: A tuple containing the `DatasetInfo`, `BrokerDetails`, and `TopicDetails` objects.

        Raises:
            NoResultFound: If no dataset is found for the provided `dataset_id`.
            IntegrityError: If there is a database integrity issue, such as duplicate or constraint violations.
            Exception: For any other unexpected errors.

        """
        try:
            response = (
                self.db_app.query(DatasetInfo, BrokerDetails, TopicDetails)
                .join(
                    DatasetTopicDetails,
                    DatasetInfo.id == DatasetTopicDetails.dataset_id,
                )
                .join(TopicDetails, DatasetTopicDetails.topic_id == TopicDetails.id)
                .join(BrokerDetails, TopicDetails.broker_id == BrokerDetails.id)
                .filter(DatasetInfo.id == dataset_id)
                .one()
            )

            response_data = self.dataset_message_response(
                response[0], response[1], response[2]
            )
            log.info("Messaging components register details %s", response_data)
            return response_data
        except NoRowFound as exp:
            log.error(
                "Integrity error: Constraint violation or duplicate data. %s",
                str(exp),
                exc_info=True,
            )
            raise NoResultFound(f"Dataset not found for the id {dataset_id}")
        except DBIntegrityError as exp:
            self.db_app.rollback()
            log.error(
                "Integrity error: Constraint violation or duplicate data. %s",
                str(exp),
                exc_info=True,
            )
            raise IntegrityError(message="Broker already Exists.", orig=exp)
        except Exception as exp:
            self.db_app.rollback()
            log.error("Unable to save Broker details %s", str(exp), exc_info=True)
            raise exp

    def dataset_message_response(
        self, dataset_detail, broker_detail, topic_detail
    ) -> DatasetBrokerTopicResponse:
        """
        dataset response retrieval
        Args:
            dataset_detail: dataset details
            broker_detail: broker details
            topic_detail: topic details

        Returns:
            DatasetBrokerTopicResponse
        """
        return DatasetBrokerTopicResponse(
            dataset=DatasetInfoDetails(
                id=dataset_detail.id,
                dataset_name=dataset_detail.dataset_name,
                description=dataset_detail.description,
                dataset_type=dataset_detail.train_and_inference_type,
                data_source_type=dataset_detail.data_source_type,
            ),
            broker_details=BrokerResponse(
                id=broker_detail.id,
                broker_name=broker_detail.broker_name,
                broker_ip=broker_detail.broker_ip,
                broker_port=broker_detail.broker_port,
                creation_date=broker_detail.creation_date,
            ),
            topic_details=TopicResponse(
                id=topic_detail.id,
                topic_name=topic_detail.topic_name,
                topic_schema=topic_detail.topic_schema,
                broker_id=topic_detail.broker_id,
                creation_date=topic_detail.creation_date,
            ),
        )

    async def update_file(self, request: DatasetUpdateBase, file: UploadFile):
        """
        Update the file associated with a dataset and modify its metadata.

        Args:
            request (DatasetUpdateBase): The request object containing dataset ID and other metadata.
            file (UploadFile): The new file to be uploaded for the dataset.

        Returns:
            DatasetUploadSchema: The updated dataset details after successful file update.

        Raises:
            FileNotFoundError: If no file is provided in the request.
            NoResultFound: If no dataset is found for the provided `dataset_id`.
            DatasetUploadExistsException: If a dataset with the same filename already exists.
            Exception: For any other unexpected errors.
        """

        try:
            if file:
                file_data = await file.read()

                # Do we need to update inference type also?
                dataset_upload = (
                    self.db_app.query(DatasetFileDetails)
                    .filter(DatasetFileDetails.dataset_id == request.id)
                    .one()
                )

                dataset_upload.register_date = datetime.utcnow()
                dataset_upload.file_name = file.filename

                # update details to model_dataset_info
                dataset_info = (
                    self.db_app.query(DatasetInfo)
                    .filter(DatasetInfo.id == request.id)
                    .one()
                )
                dataset_info.last_modified_time = datetime.utcnow()
                dataset_info.description = request.description
                dataset_info.dataset_name = request.name
                dataset_info.train_and_inference_type = request.dataset_type

                if cogflow.save_to_minio(file_data, file.filename, const.BUCKET_NAME):
                    self.db_app.commit()
                    result = DatasetUploadResponse(
                        id=dataset_upload.id,
                        dataset_id=dataset_upload.dataset_id,
                        file_path=dataset_upload.file_path,
                        file_name=dataset_upload.file_name,
                        register_date=dataset_upload.register_date,
                        description=dataset_info.description,
                        dataset_name=dataset_info.dataset_name,
                        dataset_type=dataset_info.train_and_inference_type,
                    )

                    log.info("Dataset Updated successfully %s", result)
                    return result

            log.error(" No File provided to update")
            raise FileNotFoundError("No file provided")
        except NoRowFound as exp:
            log.error(
                "Dataset not found for the id %s %s",
                request.id,
                str(exp),
                exc_info=True,
            )
            raise NoResultFound
        except Exception as exp:
            log.error("Operation Failed  %s", str(exp), exc_info=True)
            raise exp

    def fetch_table_records_for_dataset(self, dataset_id, limit) -> Dict[str, Any]:
        """
        Retrieve records from a table associated with a specific dataset.

        Args:
            dataset_id (int): The unique identifier of the dataset for which table records are requested.
            limit (int): The maximum number of records to retrieve from the table. Must be a positive integer.

        Returns:
            Dict: A dictionary containing the following keys:
                - `table_name` (str): The name of the table associated with the specified dataset.
                - `records` (List[Dict]): A list of records retrieved from the table.
                   Each record is represented as a dictionary.

        Raises:
            NoResultFound: If no dataset is found for the provided `dataset_id`.
            Exception: If the table does not exist in the database or for any other unexpected errors.
        """
        try:
            dataset_table = (
                self.db_app.query(DatasetTableDetails)
                .filter(DatasetTableDetails.dataset_id == dataset_id)
                .one()
            )

            metadata = util.DBUtils.db_engine_create(dataset_table.db_url)

            table_name = dataset_table.table_name

            if table_name not in metadata.tables.keys():
                raise Exception(f"Table '{table_name}' not found in the database.")

            table = metadata.tables[table_name]
            engine = create_engine(dataset_table.db_url)
            session = sessionmaker(bind=engine)()

            query = select([table]).limit(limit)
            records = session.execute(query).fetchall()

            # Return the records and table name in a structured format
            return {"table_name": table_name, "records": records}

        except NoRowFound as exp:
            log.error("Dataset not found. %s", str(exp), exc_info=True)
            raise NoResultFound(f"Dataset not found for the id {dataset_id}")

        except Exception as exp:
            log.error(
                "Error fetching dataset table details: %s", str(exp), exc_info=True
            )
            raise exp

    def _update_record(self, entity_obj, record_id: int, update_data, response_model):
        """
        Private method to update a record in the database.

        Args:
            entity_obj: The database model class.
            record_id: ID of the record to update.
            update_data: Pydantic model containing update fields.
            response_model: Response model to return after update.

        Returns:
            Response model instance

        Raises:
            NoRowFound: If no record is found.
            Exception: If an error occurs during the update.
        """
        try:
            record = (
                self.db_app.query(entity_obj).filter(entity_obj.id == record_id).one()
            )

            for key, value in update_data.dict(by_alias=False).items():
                if value is not None:
                    setattr(record, key, value)

            self.db_app.commit()
            self.db_app.refresh(record)
            log.info("%s updated successfully: %s", entity_obj.__name__, record)
            return response_model.from_orm(record)

        except DBIntegrityError as exp:
            log.error(
                "%s not found for ID %s: %s",
                entity_obj.__name__,
                record_id,
                str(exp),
                exc_info=True,
            )
            raise IntegrityError(
                message=f"No {entity_obj.__name__} found for ID: {record_id}", orig=exp
            )

        except NoRowFound as exp:
            log.error(
                "%s not found for ID %s: %s",
                entity_obj.__name__,
                record_id,
                str(exp),
                exc_info=True,
            )
            raise NoResultFound(f"No {entity_obj.__name__} found for ID: {record_id}")

        except Exception as exp:
            log.error(
                "Exception occurred while updating %s (ID: %s): %s",
                entity_obj.__name__,
                record_id,
                str(exp),
                exc_info=True,
            )
            raise exp

    def update_broker(
        self, broker_id: int, broker_data: BrokerUpdate
    ) -> BrokerResponse:
        """
        Updates broker details.

        Args:
            broker_id: ID of the broker to update.
            broker_data: Broker details to update.

        Returns:
            BrokerResponse: Updated broker details.
        """
        return self._update_record(
            BrokerDetails, broker_id, broker_data, BrokerResponse
        )

    def update_topic(self, topic_id: int, topic_data: TopicUpdate) -> TopicResponse:
        """
        Updates topic details.

        Args:
            topic_id: ID of the topic to update.
            broker_id : ID of the broker to update
            topic_data: Topic details to update.

        Returns:
            TopicResponse: Updated topic details.
        """

        return self._update_record(TopicDetails, topic_id, topic_data, TopicResponse)

    def fetch_dataset_topic_data(
        self, dataset_id: int, no_of_records: Optional[int], offset_reset: str
    ) -> DatasetTopicData:
        """
        Retrieve records from topic associated with a specific dataset.

        Args:
            dataset_id (int): The unique identifier of the dataset for which table records are requested.
            no_of_records (int): The maximum number of records to retrieve from the topic. Must be a positive integer.
            offset_reset (str) : To retrieve messages from the topic either earliest/latest

        Returns:
            Dict: A dictionary containing the following keys:

        Raises:
            NoResultFound: If no dataset is found for the provided `dataset_id`.
            Exception: If the topic does not exist in the database or for any other unexpected errors.
        """
        try:
            # Fetch topic and broker details from the database
            topic_details = self._get_topic_and_broker_details(dataset_id)

            # Fetch records from stream
            records = self.__fetch_stream_data(
                topic_details, offset_reset, no_of_records
            )

            # Prepare and return the result
            return DatasetTopicData(
                dataset_id=dataset_id,
                records=records,
                record_count=len(records),
                topic_name=topic_details.topic_name,
            )
        except NoRowFound as exp:
            log.error("Dataset not found. %s", str(exp), exc_info=True)
            raise NoResultFound(f"Dataset not found for ID {dataset_id}")
        except NoMessagesFound as exp:
            log.error("No messages found in the stream. %s", str(exp), exc_info=True)
            raise exp
        except Exception as exp:
            log.error("Error fetching dataset details: %s", str(exp), exc_info=True)
            raise exp

    def _get_topic_and_broker_details(self, dataset_id) -> BrokerTopicDetails:
        """
        Fetch topic and broker details associated with a specific dataset.

        Args:
            dataset_id (int): The unique identifier of the dataset for which topic and broker details are being fetched.

        Returns:
            BrokerTopicDetails: An object containing the topic name,
            broker IP and broker port for the specified dataset.

        Raises:
            NoResultFound: If no topic association is found for the provided `dataset_id` or
            if the topic or broker does not exist.
            Exception: If there is an issue retrieving the broker details, such as an invalid broker ID.

        """
        # 1. Fetch dataset-topic association
        dataset_topic_detail = (
            self.db_app.query(DatasetTopicDetails)
            .filter(DatasetTopicDetails.dataset_id == dataset_id)
            .one_or_none()
        )
        if not dataset_topic_detail:
            raise NoResultFound(f"No topic association for dataset ID: {dataset_id}")

        # 2. Fetch topic details
        topic_detail = (
            self.db_app.query(TopicDetails)
            .filter(TopicDetails.id == dataset_topic_detail.topic_id)
            .one_or_none()
        )
        if not topic_detail:
            raise NoResultFound(
                f"Topic not found for ID: {dataset_topic_detail.topic_id}"
            )

        # 3. Fetch broker details
        broker_detail = (
            self.db_app.query(BrokerDetails)
            .filter(BrokerDetails.id == topic_detail.broker_id)
            .one_or_none()
        )
        if not broker_detail:
            raise NoResultFound(f"Broker not found for ID: {topic_detail.broker_id}")

        return BrokerTopicDetails(
            topic_name=topic_detail.topic_name,
            broker_ip=broker_detail.broker_ip,
            broker_port=broker_detail.broker_port,
        )

    def __fetch_stream_data(
        self,
        topic_details: BrokerTopicDetails,
        offset_reset: str,
        no_of_records: Optional[int] = const.DEFAULT_STREAM_DATA_COUNT,
    ) -> List[Any]:
        """
        Fetches records from stream topic.

        Args:
            topic_details (BrokerTopicDetails): An object containing the
            details of topic (name, broker IP, and broker port).
            offset_reset (str): Defines the starting point for consuming records.
            It can be 'earliest' to start from
            the earliest message, or 'latest' to start from the latest message.
            no_of_records (int, optional): The maximum number of records to retrieve from the stream. Defaults to 200..

        Returns:
            List[Any]: A list containing the messages (deserialized) fetched from the topic.

        Raises:
            NoMessagesFound: If no messages are found in the topic within the specified timeout.
            Exception: For any unexpected errors encountered during the fetching of messages from the stream.

        """

        topic_name = topic_details.topic_name
        broker_ip = topic_details.broker_ip
        broker_port = topic_details.broker_port
        bootstrap_servers = [f"{broker_ip}:{broker_port}"]

        consumer = KafkaConsumer(
            topic_name,
            bootstrap_servers=bootstrap_servers,
            auto_offset_reset=offset_reset,
            value_deserializer=lambda x: json.loads(x.decode("utf-8")),
        )
        try:
            messages = consumer.poll(
                timeout_ms=const.STREAM_TIMEOUT, max_records=no_of_records
            )

            if not messages:
                raise NoMessagesFound(f"No messages in stream topic: {topic_name}")

            return [
                message.value
                for partition_messages in messages.values()
                for message in partition_messages
            ]

        except Exception as exp:
            log.error(
                "Error consuming from topic %s %s", topic_name, str(exp), exc_info=True
            )
            raise exp

        finally:
            consumer.close()

    def broker_deregister(self, broker_id: int):
        """
           Deregister a broker by its primary key.
        Args:
           broker_id (int): The primary key of the broker.

        Returns:
           Tuple[bool, str]: A tuple indicating success and a message.

        Raises:
           Exception: If the broker is not found or an error occurs.
        """
        try:
            broker_details = (
                self.db_app.query(BrokerDetails)
                .filter(BrokerDetails.id == broker_id)
                .one()
            )
            self.db_app.delete(broker_details)
            self.db_app.commit()
            log.info("Broker deleted successfully")

        except NoRowFound as exp:
            log.error(
                "Broker not found for the id %s %s",
                broker_id,
                str(exp),
                exc_info=True,
            )
            raise NoResultFound(f"Broker not found for the id {broker_id}")
        except Exception as exp:
            log.error(
                "Internal exception occurred while de-registering broker. %s",
                str(exp),
                exc_info=True,
            )
            raise exp

    def topic_deregister(self, topic_id: int):
        """
           Deregister a topic by its primary key.
        Args:
           topic_id (int): The primary key of the topic.

        Returns:
           Tuple[bool, str]: A tuple indicating success and a message.

        Raises:
           Exception: If the topic is not found or an error occurs.
        """
        try:
            topic_details = (
                self.db_app.query(TopicDetails)
                .filter(TopicDetails.id == topic_id)
                .one()
            )
            self.db_app.delete(topic_details)
            self.db_app.commit()
            log.info("Topic deleted successfully")

        except NoRowFound as exp:
            log.error(
                "Topic not found for the id %s %s",
                topic_id,
                str(exp),
                exc_info=True,
            )
            raise NoResultFound(f"Topic not found for the id {topic_id}")
        except Exception as exp:
            log.error(
                "Internal exception occurred while de-registering topic. %s",
                str(exp),
                exc_info=True,
            )
            raise exp

    def dataset_message_deregister(self, dataset_id: int):
        """
        Deregister a dataset and its related topic by their primary keys.

        Args:
            dataset_id (int): The primary key of the dataset.

        Returns:
            Tuple[bool, str]: A tuple indicating success and a message.

        Raises:
            Exception: If the dataset or topic is not found or an error occurs.
        """

        try:
            # Fetch dataset details
            dataset_details = (
                self.db_app.query(DatasetInfo)
                .filter(
                    (DatasetInfo.id == dataset_id)
                    & (DatasetInfo.data_source_type == const.BROKER_DATA_SOURCE_TYPE)
                )
                .one()
            )

            # Fetch related topic details
            topic_details = (
                self.db_app.query(DatasetTopicDetails)
                .filter(DatasetTopicDetails.dataset_id == dataset_details.id)
                .one_or_none()
            )

            # Delete topic first if it exists
            if topic_details:
                self.db_app.delete(topic_details)

            # Delete dataset
            self.db_app.delete(dataset_details)
            self.db_app.commit()

            log.info("Dataset and associated topic deleted successfully")

        except NoRowFound as exp:
            log.error(
                "Dataset not found for id %s: %s", dataset_id, str(exp), exc_info=True
            )
            raise NoResultFound(f"Dataset not found for id {dataset_id}")
        except Exception as exp:
            log.error(
                "Error occurred while deregistering dataset: %s",
                str(exp),
                exc_info=True,
            )
            self.db_app.rollback()  # Rollback in case of error
            raise exp
