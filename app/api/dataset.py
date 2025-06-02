"""
This module contains the API routes for the dataset endpoints.
"""
import re
from typing import Optional, List
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    UploadFile,
    File,
    Form,
    Query,
    Path,
    Request,
    status,
)
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.broker_details import BrokerBase, BrokerUpdate, BrokerResponse
from app.schemas.dataset_broker_topic import (
    DatasetBrokerTopicBase,
    DatasetBrokerTopicResponse,
)
from app.schemas.dataset_table_register import (
    DatasetTable,
    DatasetTableRegister,
    DatasetTypeEnum,
)
from app.schemas.dataset_upload import DatasetUploadBase, DatasetUpdateBase
from app.schemas.response import StandardResponse
from app.schemas.topic_details import TopicBase, TopicUpdate, TopicResponse, OffsetReset
from app.services.dataset_service import DatasetService
from app.utils import cog_utils as util
from app.utils.exceptions import (
    NoResultFound,
    InvalidDurationException,
    IntegrityError,
    OperationException,
    DatabaseException,
    DatasetTableExistsException,
    NoMessagesFound,
)
from app.utils.response_utils import standard_response
from config import constants as const

router = APIRouter()


@router.post(
    "/datasets/file",
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_409_CONFLICT: {"description": "Integrity Error"},
        status.HTTP_400_BAD_REQUEST: {"description": "Bad request"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Internal Server Error"},
    },
)
async def register_dataset_file(
    dataset_type: int = Form(
        ...,
        description="Must be 0 or 1 or 2. "
        "0 (train data), 1 (inference data), or 2 (both).",
    ),
    name: str = Form(...),
    description: Optional[str] = Form(None),
    files: UploadFile = File(...),
    db_app: Session = Depends(get_db),
):
    """
    Register a new dataset file.

    This endpoint allows users to register a new dataset by providing necessary metadata and uploading the dataset file.

    **Parameters:**
    - `dataset_type` (int):
        The type of the dataset in (train dataset - 0,inference dataset 1, both- 2).

    - `name` (str):
        The name of the dataset being registered.

    - `description` (Optional[str]):
        A brief description of the dataset (can be `None`).

    - `files` (UploadFile):
        The file containing the dataset to be uploaded.

    - `db_app` (Session):
        The database session, automatically provided by FastAPIs dependency injection.

    **Returns:**
    - **201 Created**: creates new model.
    - **500 Internal Server Error**: Internal Server Error.
    """
    service = DatasetService(db_app)
    try:
        request = DatasetUploadBase(
            dataset_type=DatasetTypeEnum(dataset_type),
            dataset_name=name,
            description=description,
        )
        data = await service.upload_file(request, files)
        return standard_response(
            status_code=status.HTTP_201_CREATED,
            message="File uploaded successfully.",
            data=data,
        )
    except IntegrityError as exp:
        if const.DB_UNIQUE_ERROR in str(exp.orig):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"message": "Dataset Already Exists.", "detail": str(exp.orig)},
            )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"message": exp.message, "detail": str(exp.orig)},
        )

    except ValueError as exp:
        if const.DATASET_TYPE_ERROR_MESSAGE in str(exp):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(exp),
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exp),
        )
    except Exception as exp:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exp)
        )


@router.put(
    "/datasets/file",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Dataset not found"},
        status.HTTP_409_CONFLICT: {"description": "Integrity Error"},
        status.HTTP_400_BAD_REQUEST: {"description": "Bad request"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Internal Server Error"},
    },
)
async def update_dataset_file(
    id: int = Form(..., gt=0, description="id of the dataset"),
    name: str = Form(..., description="name of the dataset"),
    description: Optional[str] = Form(None),
    dataset_type: int = Form(
        ...,
        description="Must be 0 or 1 or 2. "
        "0 (train data), 1 (inference data), or 2 (both).",
    ),
    files: UploadFile = File(...),
    db_app: Session = Depends(get_db),
):  # pylint: disable=invalid-name,redefined-builtin
    """
    Update an existing dataset file.

    This endpoint allows users to update an existing dataset by
    providing its ID, name, an optional description, and uploading a new file.

    **Parameters:**
    - `id` (int):
        The ID of the dataset to be updated. Must be greater than 0.

    - `dataset_type` (int):
    The type of the dataset in (train dataset - 0,inference dataset 1, both- 2).

    - `name` (str):
        The updated name for the dataset.

    - `description` (Optional[str]):
        A brief description of the dataset. This parameter is optional and can be `None`.

    - `files` (UploadFile):
        The new file containing the dataset to replace the existing file.

    - `db_app` (Session):
        The database session, automatically provided by FastAPI's dependency injection.

    **Returns:**
    - **200 OK**:
        Indicates that the dataset was successfully updated, and the updated data is returned.

    - **409 Conflict**:
        Returned if a dataset with the same name already exists, or if an integrity constraint is violated.

    - **500 Internal Server Error**:
        Indicates that an unexpected error occurred while processing the request.
    """

    service = DatasetService(db_app)
    try:
        request = DatasetUpdateBase(
            id=id,
            name=name,
            description=description,
            dataset_type=DatasetTypeEnum(dataset_type),
        )
        data = await service.update_file(request, files)
        return standard_response(
            status_code=status.HTTP_200_OK,
            message="File updated successfully.",
            data=data,
        )
    except NoResultFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found."
        )

    except IntegrityError as exp:
        if const.DB_UNIQUE_ERROR in exp.args[0]:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Dataset Already Exists. {str(exp)}",
            )
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exp))
    except ValueError as exp:
        if const.DATASET_TYPE_ERROR_MESSAGE in str(exp):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(exp),
            )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exp),
        )

    except Exception as exp:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exp)
        )


@router.get(
    "/datasets",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Dataset not found"},
        status.HTTP_400_BAD_REQUEST: {"description": "Bad request"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Internal Server Error"},
    },
)
async def fetch_datasets(
    request: Request,
    name: Optional[str] = None,
    id: Optional[int] = Query(None, gt=0, description="The ID of the dataset"),
    last_days: Optional[int] = Query(None, gt=0, description="Duration of the dataset"),
    db_app: Session = Depends(get_db),
):  # pylint: disable=invalid-name,redefined-builtin
    """
    Fetch datasets based on filters.

    This endpoint allows users to retrieve datasets from the database,
    with optional filtering by name, dataset ID, or a duration of the last few days.

    **Parameters:**
    - `request` (Request): The incoming HTTP request, used to manage pagination.
    - `name` (Optional[str]):
        The name of the dataset to search for. If not provided, all datasets will be considered.

    - `id` (Optional[int]):
        The primary key of the dataset. Must be greater than 0.

    - `last_days` (Optional[int]):
        The number of days to look back for datasets. Must be greater than 0.

    - `db_app` (Session):
        The database session, automatically provided by FastAPIs dependency injection.

    **Returns:**
    - **200 OK**: Fetched dataset successfully.
    - **404 Not Found**: Dataset not found.
    - **400 Bad Request**: Invalid duration provided.
    - **500 Internal Server Error**: Internal server error.

    """
    service = DatasetService(db_app)
    try:
        data = await service.search_datasets(last_days, name, id)
        if any([last_days, name, id]):
            return standard_response(
                status_code=status.HTTP_200_OK,
                message="Filtered dataset details",
                data=data,
                request=request,
            )
        return standard_response(
            status_code=status.HTTP_200_OK,
            message="All datasets",
            data=data,
            request=request,
        )
    except NoResultFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found."
        )
    except InvalidDurationException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid duration provided."
        )
    except Exception as exp:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exp)
        )


@router.delete(
    "/datasets/file/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Dataset not found"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Internal Server Error"},
    },
)
async def delete_dataset_file(
    id: int = Path(..., gt=0, description="The ID of the dataset"),
    db_app: Session = Depends(get_db),
):  # pylint: disable=invalid-name,redefined-builtin
    """
    Delete a dataset file.

    This endpoint allows users to delete a specific dataset
    from the database using its unique identifier (dataset ID).

    **Parameters:**
    - `id` (int):
        The primary key of the dataset to be deleted. Must be greater than 0.

    - `db_app` (Session):
        The database session, automatically provided by FastAPI's dependency injection.

    **Returns:**
    - **200 OK**:  deleted dataset successfully.
    - **404 Not Found**:  dataset not found.
    """
    service = DatasetService(db_app)
    try:
        data = await service.deregister_dataset(id)
        return standard_response(
            status_code=status.HTTP_200_OK,
            message="Dataset deleted successfully",
            data=data,
        )
    except NoResultFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset not found for the id {id}",
        )
    except Exception as exp:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal Exception occurred while retrieving dataset for the id {id} : {str(exp)}",
        )


@router.post(
    "/datasets/{id}/models/{mid}/link",
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Dataset or model not found"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Internal Server Error"},
    },
)
async def link_dataset_model(
    id: int = Path(..., gt=0, description="The ID of the dataset"),
    mid: int = Path(..., gt=0, description="The ID of the model"),
    db_app: Session = Depends(get_db),
):  # pylint: disable=invalid-name,redefined-builtin
    """
    Link a dataset to a model.

    This endpoint establishes a relationship between a specified dataset and
    a model by linking them using their unique identifiers.

    **Parameters:**
    - `id` (int):
        The unique identifier of the dataset to be linked. Must be greater than 0.

    - `mid` (int):
        The unique identifier of the model to be linked. Must be greater than 0.

    - `db_app` (Session):
        The database session, provided automatically by FastAPIs dependency injection.

    **Returns:**
    - **201 Created**:  linked model and dataset successfully.
    - **404 NotFound**:  Dataset or Model not found.
    - **500 Internal Server Error**: Internal server error.
    """
    service = DatasetService(db_app)
    try:
        data = await service.link_dataset_model(id, mid)
        return standard_response(
            status_code=status.HTTP_201_CREATED,
            message="Dataset linked with model successfully",
            data=data,
        )
    except NoResultFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Dataset or model not found."
        )
    except Exception as exp:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exp)
        )


@router.post(
    "/datasets/{id}/models/{mid}/unlink",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Dataset or model not found"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Internal Server Error"},
    },
)
async def unlink_dataset_model(
    id: int = Path(..., gt=0, description="The ID of the dataset"),
    mid: int = Path(..., gt=0, description="The ID of the model"),
    db_app: Session = Depends(get_db),
):  # pylint: disable=invalid-name,redefined-builtin
    """
    Unlink a dataset from a model.

    This endpoint removes the relationship between a specified dataset and
     a model by unlinking them using their unique identifiers.

    **Parameters:**
    - `id` (int):
        The unique identifier of the dataset to be unlinked. Must be greater than 0.

    - `mid` (int):
        The unique identifier of the model to be unlinked. Must be greater than 0.

    - `db_app` (Session):
        The database session, provided automatically by FastAPI's dependency injection.

    **Returns:**
    - **200 OK**: dataset and model linked successfully.
    - **404 NotFound**: dataset or model not found.
    - **500 Internal Server Error**: Internal server error.
    """
    service = DatasetService(db_app)
    try:
        data = await service.unlink_dataset_model(id, mid)
        return standard_response(
            status_code=status.HTTP_200_OK,
            message="Dataset unlinked from model successfully",
            data=data,
        )
    except NoResultFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Dataset or model not found."
        )
    except Exception as exp:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exp)
        )


@router.post(
    "/datasets/table",
    status_code=status.HTTP_201_CREATED,
    response_model=StandardResponse[DatasetTableRegister],
    responses={
        status.HTTP_409_CONFLICT: {"description": "Integrity Error"},
        status.HTTP_400_BAD_REQUEST: {"description": "Bad request"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Internal Server Error"},
    },
)
async def dataset_table_register(data: DatasetTable, db_app: Session = Depends(get_db)):
    """
    Create a new dataset table in the database.

    This endpoint registers a new dataset table with the provided details.
    It saves the dataset table information into the database and
    returns the registration details.

    **Parameters:**
    - `data` (DatasetTable):
        The dataset table information to register, which may include fields
        like `table name`, `schema`, and other relevant attributes.
    - `db_app` (Session):
        The database session, provided by FastAPIs dependency injection.

    **Returns:**
    - **201 Created**:
        A standard response containing the registration details of the created dataset table.
    - **500 Internal Server Error**: Internal server error.
    - **409 Integrity Error**: Unique/duplicate value.

    """
    service = DatasetService(db_app)
    try:
        result = await service.register_dataset_table(data)
        return standard_response(
            status_code=status.HTTP_201_CREATED,
            message="Dataset table Register Details",
            data=result,
        )
    except IntegrityError as exp:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"message": exp.message, "detail": str(exp.orig)},
        )
    except ValueError as exp:
        if const.DATASET_TYPE_ERROR_MESSAGE in str(exp):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(exp),
            )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exp),
        )
    except Exception as exp:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exp)
        )


@router.put(
    "/datasets/table",
    response_model=StandardResponse[DatasetTableRegister],
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_409_CONFLICT: {"description": "Integrity Error"},
        status.HTTP_400_BAD_REQUEST: {"description": "Bad request"},
        status.HTTP_404_NOT_FOUND: {"description": "Dataset not found"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Internal Server Error"},
    },
)
def dataset_table_update(data: DatasetTable, db_app: Session = Depends(get_db)):
    """
    Update the details of a dataset table in the database.

    This endpoint allows for updating the information of an existing dataset table.
    It modifies the dataset table with the provided details.

    **Parameters:**
    - `data` (DatasetTable):
        The dataset table information to update, including the `table name`, `schema`, and any other relevant details.
    - `db_app` (Session):
        The database session, provided automatically by FastAPIs dependency injection.

    **Returns:**
    - **200 OK**:
        A standard response containing the updated dataset table information.
    - **404 NotFound**: dataset table not registered.
    - **500 Internal Server Error**: Internal server error.
    - **409 Integrity Error**: Unique/duplicate value.

    """
    service = DatasetService(db_app)
    try:
        result = service.update_dataset_table(data)
        return standard_response(
            status_code=status.HTTP_200_OK,
            message="Dataset table Register Details Updated",
            data=result,
        )
    except NoResultFound as exp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset Not Registered. Error: {str(exp)}",
        )
    except DatasetTableExistsException as exp:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exp))
    except ValueError as exp:
        if const.DATASET_TYPE_ERROR_MESSAGE in str(exp):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(exp),
            )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exp),
        )

    except IntegrityError as exp:
        if const.DB_UNIQUE_ERROR in str(exp.orig):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "message": "Dataset table Already Exists.",
                    "detail": str(exp.orig),
                },
            )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"message": exp.message, "detail": str(exp.orig)},
        )
    except Exception as exp:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exp)
        )


@router.get(
    "/datasets/tables",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_503_SERVICE_UNAVAILABLE: {"description": "Service Unavailable"},
        status.HTTP_400_BAD_REQUEST: {"description": "Bad request"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Internal Server Error"},
    },
)
def fetch_tables(
    request: Request,
    url: str = Query(
        ..., description="db url format: dialect://username:password@host:port/database"
    ),
    db_app: Session = Depends(get_db),
):
    """
    Fetch dataset table details from the specified database.
    This endpoint retrieves a list of tables available in the given database URL.

    **Parameters:**
    - `request` (Request): The incoming HTTP request, used to manage pagination.
    - `url` (str):
        The URL of the database from which to fetch table details.
        The URL should include the necessary credentials and database information.
    - `db_app` (Session):
        The database session, provided automatically by FastAPIs dependency injection.

    **Returns:**
    - **200 OK**:
        A list of tables and their details from the specified database.
    - **503 Service unavailable**: Service unavailable.
    - **500 Internal server error**: Internal server error.
    - **400 Bad request**: Invalid url provided.

    """
    service = DatasetService(db_app)
    try:
        if not util.S3Utils.validate_db_url(url):
            raise ValueError("Invalid Url format")

        data = service.fetch_db_tables(url)
        return standard_response(
            status_code=status.HTTP_200_OK,
            message="Tables Details.",
            data=data,
            request=request,
        )

    except DatabaseException as exp:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database Exception in while fetching details: {str(exp)}",
        )

    except OperationException as exp:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Operation Error: {str(exp)}",
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid database URL format",
        )
    except Exception as exp:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal Exception: {str(exp)}",
        )


@router.post(
    "/datasets/broker",
    status_code=status.HTTP_201_CREATED,
    response_model=StandardResponse[BrokerResponse],
    responses={
        status.HTTP_409_CONFLICT: {"description": "Integrity Error"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Internal Server Error"},
    },
)
async def dataset_broker_register(data: BrokerBase, db_app: Session = Depends(get_db)):
    """
    Register Broker  details in the system.
    This endpoint saves broker information to the database.

    **Parameters:**
    - `data` (BrokerBase):
        The Broker to be registered.
        This includes fields such as `name`, `ip`  and `port`
    - `db_app` (Session):
        The database session, provided automatically by FastAPI’s dependency injection.

    **Returns:**
    - **201 Created**:
        The registered broker details if the process succeeds.
    - **409 Conflict**:
        If a broker details already exists.
    - **500 Internal Server Error**:
        In case of an internal error during the registration process.
    - **503 Service Unavailable**:
        If the service is temporarily unavailable.
    """
    service = DatasetService(db_app)
    try:
        result = service.register_broker(data)
        return standard_response(
            status_code=status.HTTP_201_CREATED,
            message="Broker created successfully.",
            data=result,
        )

    except IntegrityError as exp:
        match = re.search(r"Broker id (\d+)", str(exp.message))
        if match:
            broker_id = match.group(1)
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "message": exp.message,
                    "detail": str(exp.orig),
                    "broker_id": broker_id,
                },
            )

    except Exception as exp:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal Exception: {str(exp)}",
        )


@router.patch(
    "/datasets/broker/{id}",
    response_model=StandardResponse[BrokerResponse],
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Broker not found"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Internal Server Error"},
    },
)
async def dataset_broker_update(
    data: BrokerUpdate,
    id: int = Path(..., gt=0, description="The ID of the broker"),
    db_app: Session = Depends(get_db),
):  # pylint: disable=invalid-name,redefined-builtin
    """
    Update Broker  details in the system.
    This endpoint updates broker information to the database.

    **Parameters:**
    - `data` (BrokerUpdate):
        The Broker to be updated.
        This includes fields such as `name`, `ip` and `port`
    - `db_app` (Session):
        The database session, provided automatically by FastAPI’s dependency injection.

    **Returns:**
    - **200 Updated**:
        The updated broker details if the process succeeds.
    - **500 Internal Server Error**:
        In case of an internal error during the updating broker.
    """
    service = DatasetService(db_app)
    try:
        result = service.update_broker(id, data)
        return standard_response(
            status_code=status.HTTP_200_OK,
            message="Broker updated successfully.",
            data=result,
        )

    except NoResultFound as exp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exp))

    except IntegrityError as exp:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exp))

    except Exception as exp:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal Exception: {str(exp)}",
        )


@router.post(
    "/datasets/broker/{id}/topic",
    status_code=status.HTTP_201_CREATED,
    response_model=StandardResponse[TopicResponse],
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Topic not found"},
        status.HTTP_409_CONFLICT: {"description": "Integrity Error"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Internal Server Error"},
    },
)
async def dataset_topic_register(
    data: TopicBase,
    id: int = Path(..., gt=0, description="The ID of the broker"),
    db_app: Session = Depends(get_db),
):  # pylint: disable=invalid-name,redefined-builtin
    """
    Register a new dataset topic.

    This endpoint allows for the registration of a new topic in the system by saving topic details to the database.

    **Parameters:**
    - `data` (TopicBase):
        The topic information to be registered, including fields like `topic name` and `schema`.
    - `db_app` (Session):
        The database session, injected automatically by FastAPI.

    **Returns:**
    - **201 Created**:
        The details of the newly created topic if successful.
    - **409 Conflict**:
        If a topic already exists or violates foreign key constraints.
    - **500 Internal Server Error**:
        For general or operational errors during the registration process.
    """
    service = DatasetService(db_app)
    try:
        result = service.register_topic(id, data)
        return standard_response(
            status_code=status.HTTP_201_CREATED,
            message="Topic created successfully",
            data=result,
        )
    except NoResultFound as exp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exp),
        )

    except IntegrityError as exp:
        match = re.search(r"Topic id (\d+)", str(exp.message))
        if const.DB_UNIQUE_ERROR in str(exp.orig) and match:
            topic_id = match.group(1)
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "message": "Topic Already Exists.",
                    "detail": str(exp.orig),
                    "topic_id": topic_id,
                },
            )
        if const.DB_FOREIGN_KEY_ERROR in str(exp.orig):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "message": "Broker doesnt Exists.",
                    "detail": str(exp.orig),
                },
            )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"message": "Topic Integrity Error:", "detail": str(exp.orig)},
        )

    except Exception as exp:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal Exception: {str(exp)}",
        )


@router.patch(
    "/datasets/broker/topic/{id}",
    response_model=StandardResponse[TopicResponse],
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Topic not found"},
        status.HTTP_409_CONFLICT: {"description": "Integrity Error"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Internal Server Error"},
    },
)
async def dataset_topic_update(
    data: TopicUpdate,
    id: int = Path(..., gt=0, description="The ID of the topic"),
    db_app: Session = Depends(get_db),
):  # pylint: disable=invalid-name,redefined-builtin
    """
    Update Topic details in the system.
    This endpoint updates topic information to the database.

    **Parameters:**
    - `id` (int) - id of the topic
    - `data` (TopicUpdate):
        The Topic to be updated.
        This includes fields such as `name`, `schema` and `topic id`
    - `db_app` (Session):
        The database session, provided automatically by FastAPI’s dependency injection.

    **Returns:**
    - **200 Updated**:
        The updated topic details if the process succeeds.
    - **500 Internal Server Error**:
        In case of an internal error during the updating topic.
    """
    service = DatasetService(db_app)
    try:
        result = service.update_topic(id, data)
        return standard_response(
            status_code=status.HTTP_200_OK,
            message="Topic updated successfully.",
            data=result,
        )

    except NoResultFound as exp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exp))

    except IntegrityError as exp:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exp))

    except Exception as exp:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal Exception: {str(exp)}",
        )


@router.get(
    "/datasets/broker/details",
    status_code=status.HTTP_200_OK,
    response_model=StandardResponse[List[BrokerResponse]],
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "No Broker defined"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Internal Server Error"},
    },
)
async def fetch_broker_details(
    request: Request,
    db_app: Session = Depends(get_db),
):
    """
    Fetches the details of the broker from the database.

    **Parameters:**
    - `request` (Request): The incoming HTTP request, used to manage pagination.
    - `db_app` (Session): The database session, provided via FastAPI's dependency injection.

    **Returns:**
    - **200 OK**: Broker details along with pagination info if found.
    - **404 Not Found**: If the broker is not found.
    - **500 Internal Server Error**: In case of any other errors.
    """
    service = DatasetService(db_app)
    try:
        result = service.fetch_broker_details()
        return standard_response(
            status_code=status.HTTP_200_OK,
            message="Broker Details.",
            data=result,
            request=request,
        )

    except NoResultFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No Broker defined."
        )

    except Exception as exp:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal Exception: {str(exp)}",
        )


@router.get(
    "/datasets/topic/details",
    status_code=status.HTTP_200_OK,
    response_model=StandardResponse[List[TopicResponse]],
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "No Topic defined."},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Internal Server Error"},
    },
)
async def fetch_topic_details(
    request: Request,
    db_app: Session = Depends(get_db),
):
    """
    Fetches the details of the topic from the database.

    **Parameters:**
    - `request` (Request): The incoming HTTP request, used for handling pagination.
    - `db_app` (Session): The database session, injected by FastAPI.

    **Returns:**
    - **200 OK**: Topic details along with pagination if found.
    - **404 Not Found**: If the topic is not found.
    - **500 Internal Server Error**: In case of any other internal error.
    """
    service = DatasetService(db_app)
    try:
        result = service.fetch_topic_details()
        return standard_response(
            status_code=status.HTTP_200_OK,
            message="Topic Details.",
            data=result,
            request=request,
        )

    except NoResultFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No Topic defined."
        )

    except Exception as exp:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal Exception: {str(exp)}",
        )


@router.post(
    "/datasets/message",
    status_code=status.HTTP_201_CREATED,
    response_model=StandardResponse[DatasetBrokerTopicResponse],
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Dataset not found."},
        status.HTTP_409_CONFLICT: {"description": "Integrity Error"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Internal Server Error"},
    },
)
async def dataset_message_register(
    data: DatasetBrokerTopicBase, db_app: Session = Depends(get_db)
):
    """
    Registers dataset, broker, and topic details in the database.

    This endpoint allows the registration of a dataset along with its associated
    broker and topic details. The data provided is validated and stored in the database.
    If any database constraint violations or operational issues occur, appropriate
    HTTP exceptions are raised.

    **Parameters:**
    -    `data` (DatasetBrokerTopicBase): An object containing the
          `dataset name`,`description`,
          `dataset type` (int): The type of the dataset in (train dataset - 0,inference dataset 1, both- 2).,
          `broker information`, and `topic details`.
    -    `db_app` (Session): Database session dependency for performing database operations.

    **Returns**:
    - **404 Not Found**: If the topic is not found.
    - **500 Internal Server Error**: In case of any other internal error.

    """
    service = DatasetService(db_app)
    try:
        result = service.register_dataset_message_details(data)
        return standard_response(
            status_code=status.HTTP_200_OK,
            message="Dataset Broker Topic Details.",
            data=result,
        )
    except IntegrityError as exp:
        if const.DB_UNIQUE_ERROR in str(exp.orig):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"message": "Dataset Already Exists.", "detail": str(exp.orig)},
            )
        if const.DB_FOREIGN_KEY_ERROR in str(exp.orig):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"message": "Dataset doesnt Exists.", "detail": str(exp.orig)},
            )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"message": "Dataset Integrity Error:", "detail": str(exp.orig)},
        )
    except NoResultFound as exp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{str(exp)}")

    except Exception as exp:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal Exception: {str(exp)}",
        )


@router.get(
    "/datasets/{id}/message/details",
    response_model=StandardResponse[DatasetBrokerTopicResponse],
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Dataset not found."},
        status.HTTP_409_CONFLICT: {"description": "Integrity Error"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Internal Server Error"},
    },
)
async def fetch_dataset_message_details(
    request: Request,
    id: int = Path(gt=0, description="The ID of the dataset "),
    db_app: Session = Depends(get_db),
):  # pylint: disable=invalid-name,redefined-builtin
    """
    Fetch detailed information about a dataset along with its associated broker and topic details.

    This endpoint retrieves information about a dataset from the `dataset_info` table using the given `dataset_id`.
    It also fetches related details from:
    - `dataset_topic` to map the dataset with topics.
    - `topic_details` for topic-specific metadata.
    - `broker_details` for broker information linked to the topic.

    **Parameters:**
    - `request` (Request): The incoming HTTP request, used to manage pagination.
    -  `dataset_id` (int): The unique identifier of the dataset. Must be a positive integer.
    -  `db_app` (Session): Database session dependency for executing database queries.

    **Returns:**
    - **200 OK**:
        dataset broker topic details.
    - **404 Not Found**:
        If the dataset with the given `id` does not exist  in the database.
    - **500 Internal Server Error**:
        For any internal processing errors encountered during the retrieval process.
    """
    service = DatasetService(db_app)
    try:
        result = service.fetch_dataset_message_details(id)
        return standard_response(
            status_code=status.HTTP_200_OK,
            message="Dataset message details.",
            data=result,
            request=request,
        )
    except NoResultFound as exp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{str(exp)}")
    except IntegrityError as exp:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "message": exp.message,
                "detail": str(exp.orig),
            },
        )

    except Exception as exp:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal Exception: {str(exp)}",
        )


@router.get(
    "/datasets/{id}/file",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Dataset not found."},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Internal Server Error"},
    },
)
async def fetch_file_datasets_details(
    id: int = Path(gt=0, description="The ID of the dataset "),
    db_app: Session = Depends(get_db),
):  # pylint: disable=invalid-name,redefined-builtin
    """
    Retrieve file details associated with a specific dataset.

    This endpoint fetches details of the files registered under a given dataset identifier (`id`).
    It provides users with structured information about each file associated with the specified dataset,
    facilitating data management and integration processes.

    **Parameters:**
    - `id` (int):
        The unique identifier of the dataset whose file details are being retrieved.
        Must be a positive integer.
    - `db_app` (Session):
        The database session, automatically provided by FastAPI’s dependency injection.

    **Returns:**
    - **200 OK**:
        JSON array with details about each file registered under the specified dataset.
    - **404 Not Found**:
        If the dataset with the given `id` does not exist or has no associated files in the database.
    - **500 Internal Server Error**:
        For any internal processing errors encountered during the retrieval process.
    """
    service = DatasetService(db_app)
    try:
        result = service.fetch_file_details_for_dataset(id)
        return standard_response(
            status_code=status.HTTP_200_OK,
            message="Dataset File Details",
            data=result,
        )

    except NoResultFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found."
        )

    except Exception as exp:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal Exception: {str(exp)}",
        )


@router.get(
    "/datasets/{id}/table",
    response_model=StandardResponse[DatasetTableRegister],
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Dataset not found."},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Internal Server Error"},
    },
)
async def fetch_dataset_table_details(
    id: int = Path(gt=0, description="The ID of the dataset "),
    db_app: Session = Depends(get_db),
):  # pylint: disable=invalid-name,redefined-builtin
    """
    Retrieve table details associated with a specific dataset.

    This endpoint fetches details of the tables registered under a given dataset identifier (`id`).
    It provides users with structured information about each table associated with the specified dataset,
    facilitating data management and integration processes.

    **Parameters:**
    - `id` (int):
        The unique identifier of the dataset whose table details are being retrieved.
        Must be a positive integer.
    - `db_app` (Session):
        The database session, automatically provided by FastAPI’s dependency injection.

    **Returns:**
    - **200 OK**:
        JSON array with details about each table registered under the specified dataset.
    - **404 Not Found**:
        If the dataset with the given `id` does not exist or has no associated tables in the database.
    - **500 Internal Server Error**:
        For any internal processing errors encountered during the retrieval process.
    """
    service = DatasetService(db_app)
    try:
        result = service.fetch_table_details_for_dataset(id)
        return standard_response(
            status_code=status.HTTP_200_OK,
            message="Dataset Table Details",
            data=result,
        )

    except NoResultFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found."
        )

    except Exception as exp:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal Exception:{str(exp)}",
        )


@router.get(
    "/datasets/{id}/table/records",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Dataset not found."},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Internal Server Error"},
    },
)
async def fetch_table_records_for_datasets(
    id: int = Path(gt=0, description="The ID of the dataset "),
    limit: Optional[int] = Query(None, gt=0, description="Duration of the dataset"),
    db_app: Session = Depends(get_db),
):  # pylint: disable=invalid-name,redefined-builtin
    """
    Retrieve records from a table associated with a specific dataset.

    This endpoint fetches a specified number of records from a table
    linked to the provided dataset identifier (`id`).
    It allows users to retrieve table records based on a dataset,
    supporting pagination through the `limit` query parameter.

    **Parameters:**
    - `id` (int):
        The unique identifier of the dataset whose table records are being fetched.
        Must be a positive integer.
    - `limit` (Optional[int]):
        The maximum number of records to retrieve. If not provided, all available records will be fetched.
        Must be a positive integer if specified.
    - `db_app` (Session):
        The database session, automatically provided by FastAPI’s dependency injection.

    **Returns:**
    - **200 OK**:
        JSON array containing the records from the table associated with the specified dataset.
    - **404 Not Found**:
        If the dataset with the given `id` does not exist or has no associated records in the database.
    - **500 Internal Server Error**:
        For any internal processing errors encountered during the retrieval process.
    """
    service = DatasetService(db_app)
    try:
        result = service.fetch_table_records_for_dataset(id, limit)
        return standard_response(
            status_code=status.HTTP_200_OK, message="Dataset Table Records", data=result
        )

    except NoResultFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found."
        )

    except Exception as exp:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal Exception:{str(exp)}",
        )


@router.get("/datasets/{id}/topic/data")
async def fetch_datasets_topic_data(
    id: int = Path(gt=0, description="The ID of the dataset "),
    no_of_records: Optional[int] = Query(
        None, gt=0, description="no of records to fetch"
    ),
    offset_reset: OffsetReset = Query(
        const.LATEST, description="Fetch latest or earliest messages"
    ),
    db_app: Session = Depends(get_db),
):  # pylint: disable=invalid-name,redefined-builtin
    """
    Retrieve topic-related data for a specific dataset.

    This endpoint retrieves a list of data records associated with the provided
    dataset identifier (`id`). The response can be retrieved using the optional
    `no_of_records` query parameter, which allows users to specify the maximum number
    of records to be returned.
    `offset_reset`: The records to be fetched from earliest/latest

    **Parameters:**
    - `id` (int):
        The unique identifier of the dataset. This ID must be a positive integer and
        is used to retrieve the dataset's associated topic data.
    - `no_of_records` (Optional[int]):
        The maximum number of records to retrieve from the dataset. If not specified,
        the default dataset topic data will be returned i.e 200 records.
        Must be a positive integer if provided.
    - `offset_reset` (Optional[str]):
        To fetch the data either earliest or latest. If not specified,
        the latest data will be returned.
    - `db_app` (Session):
        The database session, which is automatically injected by FastAPI’s dependency
        injection system. It is used to interact with the database to retrieve dataset
        records.

    **Returns:**
    - **200 OK**:
        A JSON array containing the topic data records associated with the specified
        dataset. If the `no_of_records` parameter is provided, the number of records returned
        will be limited to the specified value.
    - **404 Not Found**:
        If the dataset with the given `id` does not exist or if no data records are
        found for the provided dataset, a `404 Not Found` response will be returned.
    - **500 Internal Server Error**:
        If an internal error occurs during the processing of the request, a
        `500 Internal Server Error` response will be returned, including details of
        the exception encountered.

    **Example:**
    - Request: `GET /datasets/1/topic/data?no_of_records=10&offset_reset=earliest`
    - Response (200 OK):
    ```json

        {
    "dataset_id": 2,
    "records": [
      {
        "number": 14,
        "timestamp": 1741333467.28813
      }
    ],
    "record_count": 1,
    "topic_name": "metrics"
    },
        ...

    ```
    """
    service = DatasetService(db_app)
    try:
        result = service.fetch_dataset_topic_data(id, no_of_records, offset_reset)
        return standard_response(
            status_code=status.HTTP_200_OK, message="Topic Data", data=result
        )

    except NoResultFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found."
        )

    except NoMessagesFound as exp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exp))

    except Exception as exp:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal Exception:{str(exp)}",
        )


@router.delete(
    "/datasets/broker/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_broker",
    responses={
        status.HTTP_204_NO_CONTENT: {"description": "Broker deleted successfully"},
        status.HTTP_404_NOT_FOUND: {"description": "Broker not found"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Internal Server Error"},
    },
)
async def delete_broker(
    id: int = Path(..., gt=0, description="The ID of the broker"),
    db_app: Session = Depends(get_db),
):  # pylint: disable=invalid-name,redefined-builtin
    """
    Delete the broker by its primary key.

    This endpoint allows users to delete a specific broker
    from the database using its unique identifier (broker ID).

    **Parameters:**
    - `id` (int):
        The primary key of the broker to be deleted. Must be greater than 0.

    - `db_app` (Session):
        The database session, automatically provided by FastAPI's dependency injection.

    **Returns:**
    - **204 NO_CONTENT**:  deleted broker successfully.
    - **404 Not_Found**:  broker not found.
    """
    service = DatasetService(db_app)
    try:
        service.broker_deregister(id)
    except NoResultFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Broker not found for the id {id}",
        )
    except Exception as exp:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal Exception occurred while retrieving broker for the id {id} : {str(exp)}",
        )


@router.delete(
    "/datasets/topic/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_topic",
    responses={
        status.HTTP_204_NO_CONTENT: {"description": "Topic deleted successfully"},
        status.HTTP_404_NOT_FOUND: {"description": "Topic not found"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Internal Server Error"},
    },
)
async def delete_topic(
    id: int = Path(..., gt=0, description="The ID of the topic"),
    db_app: Session = Depends(get_db),
):  # pylint: disable=invalid-name,redefined-builtin
    """
    Delete the topic by its primary key.

    This endpoint allows users to delete a specific topic
    from the database using its unique identifier (topic ID).

    **Parameters:**
    - `id` (int):
        The primary key of the topic to be deleted. Must be greater than 0.

    - `db_app` (Session):
        The database session, automatically provided by FastAPI's dependency injection.

    **Returns:**
    - **204 NO_CONTENT**:  deleted topic successfully.
    - **404 Not_Found**:  topic not found.
    """
    service = DatasetService(db_app)
    try:
        service.topic_deregister(id)

    except NoResultFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Topic not found for the id {id}",
        )
    except Exception as exp:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal Exception occurred while retrieving topic for the id {id} : {str(exp)}",
        )


@router.delete(
    "/datasets/message/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_dataset_message",
    responses={
        status.HTTP_204_NO_CONTENT: {
            "description": "Dataset Message Broker details deleted success"
        },
        status.HTTP_404_NOT_FOUND: {"description": "Dataset Message not found"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Internal Server Error"},
    },
)
async def delete_dataset_message(
    id: int = Path(..., gt=0, description="The ID of the dataset message"),
    db_app: Session = Depends(get_db),
):  # pylint: disable=invalid-name,redefined-builtin
    """
    Delete the dataset by its primary key.

    This endpoint allows users to delete a specific dataset message
    from the database using its unique identifier (dataset ID).

    **Parameters:**
    - `id` (int):
        The primary key of the dataset to be deleted. Must be greater than 0.

    - `db_app` (Session):
        The database session, automatically provided by FastAPI's dependency injection.

    **Returns:**
    - **204 NO_CONTENT**:  deleted dataset successfully.
    - **404 Not_Found**:  dataset not found.
    """
    service = DatasetService(db_app)
    try:
        service.dataset_message_deregister(id)
        return standard_response(
            status_code=status.HTTP_200_OK,
            message="Dataset Message deleted successfully",
            data=None,
        )
    except NoResultFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset not found for the id {id}",
        )
    except Exception as exp:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal Exception occurred while retrieving dataset for the id {id} : {str(exp)}",
        )
