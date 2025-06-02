"""
API endpoints for managing models.

This module provides endpoints for registering new models and retrieving existing models.
"""

from typing import Optional, List

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    File,
    Form,
    UploadFile,
    Query,
    Request,
    Path,
    status,
)
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.model_dataset import ModelDetailedResponse
from app.schemas.model_info import (
    ModelInfoBase,
    ModelInfo,
    ModelDeploy,
    ModelUri,
    ModelInfoUpdate,
)
from app.schemas.model_upload import (
    ModelFileUpload,
    ModelFileUploadGet,
    ModelFileUploadPost,
    ModelFileUploadPut,
    ModelUploadUriPost,
    ModelFileTypeEnum,
)
from app.schemas.response import StandardResponse
from app.services.model_register_service import ModelRegisterService
from app.utils.exceptions import (
    NoResultFound,
    ModelFileExistsException,
    OperationException,
    ModelFileNotFoundException,
    ModelNotFoundException,
    IntegrityError,
    MinioClientError,
    InvalidDurationException,
    InvalidValueException,
)
from app.utils.response_utils import standard_response
from config import constants as const

router = APIRouter()


@router.post(
    "/models",
    response_model=StandardResponse[ModelInfo],
    status_code=status.HTTP_201_CREATED,
    operation_id="register_model",
    responses={
        status.HTTP_201_CREATED: {"description": "Model created successfully"},
        status.HTTP_400_BAD_REQUEST: {"description": "Bad request"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Internal Server Error"},
    },
)
async def register_model(data: ModelInfoBase, db_app: Session = Depends(get_db)):
    """
    Register a new model.

    Args:
        data (ModelInfoBase): The model information to register.
        db (Session): The database session.

    Returns:
        StandardResponse[ModelInfo]: The standard response containing the registered model information.
        :param db_app:
    """
    service = ModelRegisterService(db_app)
    try:
        data = service.register_model(data)
        return standard_response(
            status_code=status.HTTP_201_CREATED, message="Created new model.", data=data
        )
    except OperationException as exp:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exp))
    except Exception as exp:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal Server Error: {str(exp)}",
        )


@router.get("/models", response_model=StandardResponse[List[ModelInfo]])
async def get_models(
    request: Request,
    db_app: Session = Depends(get_db),
    id: Optional[int] = Query(None, gt=0, description="The ID of the model"),
    last_days: Optional[int] = Query(
        None, gt=0, description="Duration filter to fetch models"
    ),
    name: str = "",
):  # pylint: disable=invalid-name,redefined-builtin
    """
    API route to retrieve models based on provided filters.

    This endpoint allows you to fetch models by specifying various filtering criteria.

    **Parameters:**
    - `request` (Request):
        The request object containing request details.
    - `db_app` (Session):
        The database session, automatically provided by FastAPIs dependency injection.
    - `id` (Optional[int]):
        The ID of the model to retrieve. Defaults to None.
    - `last_days` (Optional[int]):
        Duration filter in days to fetch models. Defaults to None.
    - `name` (str):
        The name of the model to retrieve. Defaults to an empty string.

    **Behavior:**
    - If `id` is provided, it returns the model with the specified ID.
    - If `last_days` is provided, it filters models based on the specified duration.
    - If `name` is provided, it filters models based on the specified name.
    - If no filters are provided, it returns all available models.

    **Responses:**
    - **200 OK**: Returns a successful response with the list of models.
    - **404 Not Found**: Raised if no models are found matching the criteria.
    - **500 Internal Server Error**: Raised for any unexpected errors.

    """
    service = ModelRegisterService(db_app)
    try:
        data: List[ModelInfo] = service.get_model_details(
            last_days=last_days, model_pk=id, name=name
        )
        if any([last_days, name, id]):
            return standard_response(
                status_code=status.HTTP_200_OK,
                message="Filtered Models retrieved successfully.",
                data=data,
                request=request,
            )
        return standard_response(
            status_code=status.HTTP_200_OK,
            message="Models retrieved successfully.",
            data=data,
            request=request,
        )
    except NoResultFound as exp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exp))
    except InvalidDurationException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid duration provided."
        )
    except OperationException as exp:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exp))
    except Exception as exp:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal Server Error: {str(exp)}",
        )


@router.delete(
    "/models/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_model",
    responses={
        status.HTTP_204_NO_CONTENT: {"description": "Model deleted successfully"},
        status.HTTP_404_NOT_FOUND: {"description": "Model not found"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Internal Server Error"},
    },
)
async def delete_model(
    id: int = Path(..., gt=0, description="The ID of the model"),
    db_app: Session = Depends(get_db),
):  # pylint: disable=invalid-name,redefined-builtin
    """
    API route to delete a model by its ID.

    This endpoint allows you to delete a specified model from the database.

    **Parameters:**
    - `id` (int):
        The ID of the model to delete. Must be greater than 0.
    - `db_app` (Session):
        The database session, automatically provided by FastAPIs dependency injection.

    **Behavior:**
    - If the model with the specified ID exists, it will be deleted from the database.
    - If the model does not exist, an error will be raised.
    - If the provided `id` is invalid (less than or equal to 0), an error will be raised.

    **Responses:**
    - **204 OK**: Returns a successful response indicating the model has been deleted.
    - **404 Not Found**: Raised if no model is found with the specified ID or if an invalid ID is provided.
    - **400 Bad Request**: Raised for invalid operation exceptions.
    - **500 Internal Server Error**: Raised for any unexpected errors.

    """
    service = ModelRegisterService(db_app)
    try:
        if id <= 0:
            raise InvalidValueException("Invalid value provided")
        service.delete_model(id)

    except InvalidValueException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid Input :Provide Non negative value",
        )
    except NoResultFound as exp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exp))
    except OperationException as exp:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exp))
    except Exception as exp:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal Server Error: {str(exp)}",
        )


@router.patch("/models/{id}", response_model=StandardResponse[ModelInfo])
async def update_model(
    data: ModelInfoUpdate,
    id: int = Path(..., gt=0, description="The ID of the model"),
    db_app: Session = Depends(get_db),
):  # pylint: disable=invalid-name,redefined-builtin
    """
    API route to update a model by its ID.

    This endpoint allows you to update the information of a specified model in the database.

    **Parameters:**
    - `id` (int):
        The ID of the model to update. Must be greater than 0.
    - `data` (ModelInfoBase):
        The updated model information containing the new values.
    - `db_app` (Session):
        The database session, automatically provided by FastAPIs dependency injection.

    **Behavior:**
    - If the model with the specified ID exists, its information will be updated with the provided data.
    - If the model does not exist, an error will be raised.
    - If the provided `id` is invalid (less than or equal to 0), an error will be raised.

    **Responses:**
    - **200 OK**: Returns a successful response indicating the model has been updated.
    - **404 Not Found**: Raised if no model is found with the specified ID or if an invalid ID is provided.
    - **400 Bad Request**: Raised for invalid operation exceptions.
    - **500 Internal Server Error**: Raised for any unexpected errors.

    """
    service = ModelRegisterService(db_app)
    try:
        if id <= 0:
            raise InvalidValueException("Invalid value provided")
        result = service.update_model(id, data)
        return standard_response(
            status_code=status.HTTP_200_OK,
            message="Model updated successfully.",
            data=result,
        )
    except InvalidValueException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid Input :Provide Non negative value",
        )
    except NoResultFound as exp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exp))
    except OperationException as exp:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exp))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )


@router.get(
    "/models/{id}/associations",
    response_model=StandardResponse[List[ModelDetailedResponse]],
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"description": "Validation Error"},
        status.HTTP_404_NOT_FOUND: {"description": "Model Id not found"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Internal Server Error"},
    },
)
async def get_model_associations_by_id(
    id: int = Path(..., gt=0, description="The ID of the model"),
    db_app: Session = Depends(get_db),
):  # pylint: disable=invalid-name,redefined-builtin
    """
    Retrieve model and its associated details by ID

    This endpoint uses a path parameter model ID.

    Args:
        id [int]: The ID of the model to retrieve.

    Returns:
        StandardResponse[List[ModelDetailedResponse]]: The standard response containing the
        model and its associated details.
    """
    try:
        service = ModelRegisterService(db_app)
        data = service.fetch_model_with_datasets(model_id=id)
        return standard_response(
            status_code=status.HTTP_200_OK, message="Model Associations", data=data
        )

    except NoResultFound as exp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exp))
    except Exception as exp:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal Server Error: {str(exp)}",
        )


@router.get(
    "/models/associations",
    response_model=StandardResponse[List[ModelDetailedResponse]],
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"description": "Validation Error"},
        status.HTTP_404_NOT_FOUND: {"description": "Model name not found"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Internal Server Error"},
    },
)
async def get_model_associations_by_name(
    name: str = Query(..., description="The name of the model to search for"),
    db_app: Session = Depends(get_db),
):
    """
    Retrieve models and their associated details by name

    This endpoint allows searching for models by name using a partial match.

    Args:
        name [str]: The name of the model to search for (supports partial matching).

    Returns:
        StandardResponse[List[ModelDetailedResponse]]: The standard response containing the
        models and their associated details.
    """
    try:
        service = ModelRegisterService(db_app)
        data = service.fetch_model_with_datasets_by_name(model_name=name)
        return standard_response(
            status_code=status.HTTP_200_OK,
            message="Model Associations by Name",
            data=data,
        )

    except NoResultFound as exp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exp))
    except OperationException as exp:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exp)
        )
    except Exception as exp:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal Server Error: {str(exp)}",
        )


@router.post(
    "/models/{id}/file",
    response_model=StandardResponse[ModelFileUpload],
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_409_CONFLICT: {"description": "Integrity Error"},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"description": "Validation Error"},
        status.HTTP_400_BAD_REQUEST: {"description": "Bad request"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Internal Server Error"},
    },
)
async def upload_model_file(
    id: int = Path(..., gt=0, description="The ID of the model"),
    file_type: int = Form(
        ...,
        description="Must be 0 or 1. "
        "0 - Model Policy File Upload , 1 - Model File Upload",
    ),
    file_description: Optional[str] = Form(None),
    files: UploadFile = File(...),
    db_app: Session = Depends(get_db),
):  # pylint: disable=invalid-name,redefined-builtin
    """
    Upload a file to a specific model.

    This RESTful endpoint allows you to upload a file associated with a specified model.
    The model is identified by its ID in the URL path, following RESTful design principles.

    **RESTful Design:**
    - Uses HTTP POST method for creating a new resource (file upload)
    - Uses path parameter for resource identification (model ID)
    - Returns appropriate HTTP status codes
    - Provides clear error messages

    **Parameters:**
    - `id` (int):
        The ID of the model, specified in the URL path. Must be greater than 0.
    - `file_type` (int):
        The type of the file being uploaded (0 - Model Policy File, 1 - Model File).
    - `file_description` (Optional[str]):
        A description of the file. Optional.
    - `files` (UploadFile):
        The file to upload. Must not be empty.

    **File Validation:**
    - Validates that the file is not empty

    **Responses:**
    - **201 Created**: File successfully uploaded. Returns details of the uploaded file.
    - **404 Not Found**:
        - If the specified model ID does not exist
        - If there are file-related errors
    - **409 Conflict**:
        - If there are database conflicts (e.g., foreign key violations)
        - If the file already exists
    - **422 Unprocessable Entity**:
        - If the request contains invalid data
        - If the files field is missing or empty (Pydantic validation)
    - **500 Internal Server Error**: For any unexpected server errors.

    """
    service = ModelRegisterService(db_app)
    try:
        model_upload_request = ModelFileUploadPost(
            model_id=id,
            file_type=ModelFileTypeEnum(file_type),
            file_description=file_description,
        )
        result = service.upload_model_file(model_upload_request, files)
        return standard_response(
            status_code=status.HTTP_201_CREATED,
            message="File uploaded successfully.",
            data=result,
        )

    except OperationException as exp:
        if const.DB_FOREIGN_KEY_ERROR in exp.args[0]:
            detail = f"Model doesnt exists: {str(exp)}"

        elif const.DB_UNIQUE_ERROR in exp.args[0]:
            detail = f"Model File already exists: {str(exp)}"
        else:
            detail = f"Integrity error: {str(exp)}"

        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail)
    except NoResultFound as exp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No Model Id found: {str(exp)}",
        )
    except FileNotFoundError as exp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"FileNotFoundError: {str(exp)}",
        )
    except MinioClientError as exp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"MinioClient Error: {str(exp)}",
        )
    except ValueError as exp:
        if str(exp) == const.MODEL_TYPE_ERROR_MESSAGE:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(exp),
            )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Validation error: {str(exp)}",
        )
    except Exception as exp:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal Server Error: {str(exp)}",
        )


@router.put("/models/file/version", response_model=StandardResponse[ModelFileUpload])
async def update_model_file(
    model_id: int = Form(..., gt=0),
    file_id: int = Form(..., gt=0),
    file_description: Optional[str] = Form(None),
    files: UploadFile = File(...),
    db_app: Session = Depends(get_db),
):
    """
    API route to update a model file.

    This endpoint allows you to update an existing model file associated with a specified model in the database.

    **Parameters:**
    - `model_id` (int):
        The ID of the model. Must be greater than 0.
    - `file_id` (int):
        The ID of the model file. Must be greater than 0.
    - `file_description` (Optional[str]):
        A description of the file. Defaults to None if not provided.
    - `files` (UploadFile):
        The file to upload.
    - `db_app` (Session):
        The database session, automatically provided by FastAPIs dependency injection.

    **Behavior:**
    - The specified model ID and file ID must exist in the database.
    - The function handles various exceptions and provides relevant error messages.
    - On successful update, it returns the details of the updated file.

    **Responses:**
    - **200 OK**: Returns a successful response indicating the file has been updated.
    - **404 Not Found**: Raised if the model or file ID does not exist, or if there are file-related errors.
    - **409 Conflict**: Raised if the updated model file already exists.
    - **500 Internal Server Error**: Raised for any unexpected errors.

    """
    service = ModelRegisterService(db_app)
    try:
        model_upload_request = ModelFileUploadPut(
            id=file_id, model_id=model_id, file_description=file_description
        )
        result = service.update_model_file(model_upload_request, files)
        return standard_response(
            status_code=status.HTTP_200_OK,
            message="File updated successfully.",
            data=result,
        )
    except ModelFileNotFoundException as exp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model File doesnt exist : {str(exp)}",
        )
    except ModelNotFoundException as exp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model Id not found : {str(exp)}",
        )
    except FileNotFoundError as exp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"FileNotFoundError: {str(exp)}",
        )
    except ModelFileExistsException as exp:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"ModelFileExistsException: {str(exp)}",
        )
    except MinioClientError as exp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"MinioClient Error: {str(exp)}",
        )
    except Exception as exp:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal Server Error: {str(exp)}",
        )


@router.get(
    "/models/file/{name}/details", response_model=StandardResponse[ModelFileUpload]
)
async def fetch_model_file_details(
    name: str,
    model_id: int = Query(..., gt=0, description="The ID of the model"),
    db_app: Session = Depends(get_db),
):
    """
    API route to fetch details of a specific model file.

    This endpoint retrieves information about a model file associated with a specified model.

    **Parameters:**
    - `name` (str):
        The name of the model file to fetch.
    - `model_id` (int):
        The ID of the model. Must be greater than 0.
    - `db_app` (Session):
        The database session, automatically provided by FastAPIs dependency injection.

    **Behavior:**
    - The function checks for the existence of the specified model and file name.
    - If found, it returns the details of the model file.
    - Handles exceptions for model not found and general server errors.

    **Responses:**
    - **200 OK**: Returns a successful response with the model file details.
    - **404 Not Found**: Raised if the model or file name does not exist.
    - **500 Internal Server Error**: Raised for any unexpected errors.

    """
    service = ModelRegisterService(db_app)
    try:
        model_upload_request = ModelFileUploadGet(model_id=model_id, file_name=name)
        result = service.get_model_file_details(model_upload_request)
        return standard_response(
            status_code=status.HTTP_200_OK, message="Model File Details.", data=result
        )
    except ModelNotFoundException as exp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exp))
    except Exception as exp:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal Server Error: {str(exp)}",
        )


@router.delete("/models/file/{id}")
async def delete_model_file(
    id: int = Path(..., gt=0, description="The ID of the model file to delete"),
    db_app: Session = Depends(get_db),
):  # pylint: disable=invalid-name,redefined-builtin
    """
    API route to delete a model file by its ID.

    This endpoint allows for the removal of a specific model file associated with its ID.

    **Parameters:**
    - `id` (int):
        The ID of the model file to delete. Must be greater than 0.
    - `db_app` (Session):
        The database session, automatically provided by FastAPI's dependency injection.

    **Behavior:**
    - The function checks if the specified model file exists.
    - If found, the model file is deleted.
    - Handles exceptions for file not found and general server errors.

    **Responses:**
    - **200 OK**: Returns a successful response indicating that the model file has been deleted.
    - **404 Not Found**: Raised if the model file does not exist.
    - **500 Internal Server Error**: Raised for any unexpected errors.

    """
    service = ModelRegisterService(db_app)
    try:
        data = service.delete_model_file(id)
        return standard_response(
            status_code=status.HTTP_200_OK,
            message="Model File Deleted Successfully.",
            data=data,
        )
    except NoResultFound as exp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Model not Found: {str(exp)}"
        )
    except MinioClientError as exp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Minio Client Error: {str(exp)}",
        )
    except Exception as exp:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal Server Error: {str(exp)}",
        )


@router.get("/models/file")
async def download_model_file(
    model_id: Optional[int] = Query(None, description="The id of the model", gt=0),
    model_name: str = Query("", description="The name of the model"),
    db_app: Session = Depends(get_db),
):
    """
    API route to download a model file based on model ID or name.

    This endpoint allows you to retrieve a specific model file associated with the given model ID or name.

    **Parameters:**
    - `model_id` (Optional[int]):
        The ID of the model. Must be greater than 0. Defaults to None.
    - `model_name` (str):
        The name of the model. Defaults to an empty string.
    - `db_app` (Session):
        The database session, automatically provided by FastAPIs dependency injection.

    **Behavior:**
    - If both `model_id` and `model_name` are not provided, a ValueError is raised.
    - The function attempts to download the model file using the provided parameters.

    **Responses:**
    - **200 OK**: Returns the model file data if found.
    - **404 Not Found**: Raised if the model file does not exist.
    - **400 Bad Request**: Raised if neither model ID nor model name is provided.
    - **500 Internal Server Error**: Raised for any unexpected errors.

    """
    service = ModelRegisterService(db_app)
    try:
        if model_id is None and model_name is None:
            raise ValueError

        data = service.download_model_file(model_id, model_name)
        return data
    except NoResultFound as exp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Model not Found: {str(exp)}"
        )
    except MinioClientError as exp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Minio Client Error: {str(exp)}",
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please provide either model_id or model_name.",
        )
    except Exception as exp:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal Server Error: {str(exp)}",
        )


@router.post(
    "/models/uri",
    response_model=StandardResponse[ModelFileUpload],
    status_code=status.HTTP_201_CREATED,
)
async def register_model_uri(
    data: ModelUploadUriPost, db_app: Session = Depends(get_db)
):
    """
    API route to save the model URI to the database.

    This endpoint allows you to register a model URI with the associated model information.

    **Parameters:**
    - `data` (ModelUploadUriPost):
        The model URI information to register, including the necessary details for the model.
    - `db_app` (Session):
        The database session, automatically provided by FastAPIs dependency injection.

    **Responses:**
    - **201 Created**: Returns a successful response indicating the model URI has been registered.
    - **409 Conflict**: Raised if there is a conflict, such as a foreign key violation or unique constraint violation.
    - **404 Not Found**: Raised if there are issues related to the Minio client or if model information does not exist.
    - **500 Internal Server Error**: Raised for any unexpected errors.

    """
    service = ModelRegisterService(db_app)
    try:
        result = service.register_model_uri(data)
        return standard_response(
            status_code=status.HTTP_201_CREATED,
            message="Model uri Registered successfully.",
            data=result,
        )

    except IntegrityError as exp:
        if const.DB_FOREIGN_KEY_ERROR in str(exp.orig):
            detail = {"message": "Model doesnt exists:", "detail": str(exp.orig)}

        elif const.DB_UNIQUE_ERROR in str(exp.orig):
            detail = {"message": "Model File already exists:", "detail": str(exp.orig)}
        else:
            detail = {"message": "Integrity error:", "detail": str(exp.orig)}
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail)

    except MinioClientError as exp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Minio Client Error: {str(exp)}",
        )

    except NoResultFound as exp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model Info doesnt exists: {str(exp)}",
        )

    except Exception as exp:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal Server Error: {str(exp)}",
        )


@router.get(
    "/models/uri", response_model=StandardResponse[str], status_code=status.HTTP_200_OK
)
async def fetch_model_uri(
    uri: str = Query(..., description="Uri Format: s3://bucket-name/path/to/model"),
    db_app: Session = Depends(get_db),
):
    """
    Retrieves model information based on its URI.

    This endpoint accepts a model's URI, validates the URI,
    and returns the model ID associated with that URI.

    **Parameters:**
    - `uri` (str):
        The URI of the model in the format `s3://bucket-name/path/to/model`.
    - `db_app` (Session):
        The database session, automatically provided by FastAPIs dependency injection.

    **Responses:**
    - **200 OK**: Returns a successful response with the model ID associated with the given URI.
    - **404 Not Found**: Raised if no model information is found for the provided URI.
    - **500 Internal Server Error**: Raised for any unexpected errors.

    """
    service = ModelRegisterService(db_app)
    try:
        result = service.fetch_model_uri(uri)
        return standard_response(
            status_code=status.HTTP_200_OK,
            message="Model Uri retrieved successfully.",
            data=result,
        )
    except NoResultFound as exp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No Models uri details found: {str(exp)}",
        )
    except Exception as exp:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal Server Error: {str(exp)}",
        )


@router.post(
    "/models/save",
    response_model=StandardResponse[ModelInfo],
    status_code=status.HTTP_201_CREATED,
)
async def save_model_details(
    name: str = Form(...),
    file_type: int = Form(...),
    description: str = Form(None),
    files: UploadFile = File(...),
    db_app: Session = Depends(get_db),
):
    """
    Register a model in Cogflow using the model file.

    This endpoint performs the following actions:
    1. Logs the model in Cogflow.
    2. Saves model details in the database.
    3. Saves model upload details.

    **Parameters:**
    - `name` (str):
        The name of the model to register.
    - `file_type` (int):
        The type of the file being uploaded.
    - `description` (str, optional):
        A brief description of the model.
    - `files` (UploadFile):
        The files to be saved.
    - `db_app` (Session):
        The database session, provided automatically by FastAPI's dependency injection.

    **Returns:**
    - **201 Created**: A standard response containing the created model file details.
    - **500 Internal Server Error**: Raised for any unexpected errors.
    """

    service = ModelRegisterService(db_app)
    try:
        model_info_request = ModelUri(
            name=name,
            file_type=ModelFileTypeEnum(file_type),
            description=description,
        )
        data = service.log_model_in_cogflow(model_info_request, files)
        return standard_response(
            status_code=status.HTTP_201_CREATED,
            message="Model Registered in Cogflow Successfully.",
            data=data,
        )
    except NoResultFound as exp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Model not Found: {str(exp)}"
        )
    except MinioClientError as exp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Minio Client Error: {str(exp)}",
        )
    except Exception as exp:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal Server Error: {str(exp)}",
        )


@router.post("/models/service/deploy", status_code=status.HTTP_201_CREATED)
async def deploy_model_to_cogflow(data: ModelDeploy, db_app: Session = Depends(get_db)):
    """
    Deploy a model to Cogflow.

    This endpoint initiates the deployment of a specified model into the Cogflow system.

    **Parameters:**
    - `data` (ModelDeploy):
        Contains the model deployment information,
        including the model name and any other necessary parameters for deployment.
    - `db_app` (Session):
        The database session, provided automatically by FastAPIs dependency injection.

    **Returns:**
    - **201 Created**: Returns a response indicating that the model has been successfully deployed.
    - **500 Internal Server Error**: Raised for any unexpected errors.
    """
    service = ModelRegisterService(db_app)
    try:
        response = service.deploy_model(data)
        return standard_response(
            status_code=status.HTTP_201_CREATED,
            message="Model deployed in Cogflow Successfully.",
            data=response,
        )
    except Exception as exp:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal Server Error: {str(exp)}",
        )


@router.delete("/models/service/undeploy")
async def undeploy_model(
    svc_name: str = Query(
        ..., description="The name of the inference service to undeploy"
    ),
    db_app: Session = Depends(get_db),
):
    """
    API route to undeploy a served model by its name.

    This endpoint removes the specified inference service from deployment.

    **Parameters:**
    - `svc_name` (str):
        The name of the inference service to undeploy. This is a required parameter.
    - `db_app` (Session):
        The database session, automatically provided by FastAPIs dependency injection.

    **Responses:**
    - **200 OK**: Returns a successful response indicating the inference service was deleted.
    - **404 Not Found**: Raised if no service name is provided.
    - **500 Internal Server Error**: Raised for any unexpected errors.

    """
    service = ModelRegisterService(db_app)
    try:
        response = service.undeploy_model(svc_name)
        if response == "Service name is required.":
            return standard_response(
                status_code=status.HTTP_404_NOT_FOUND,
                message="No Input provided.",
                data=response,
            )
        return standard_response(
            status_code=status.HTTP_200_OK,
            message="Inference service Deleted Successfully.",
            data=response,
        )

    except Exception as exp:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal Server Error: {str(exp)}",
        )
