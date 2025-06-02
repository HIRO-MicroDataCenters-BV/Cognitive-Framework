"""
API endpoints for managing validation metrics and artifacts.

This module provides endpoints for operations on validation metrics and artifacts.
"""

from typing import Optional, List

from fastapi import APIRouter, HTTPException, Request, Query, status, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import Session
from awscli.customizations.s3.utils import split_s3_bucket_key
from botocore.exceptions import ClientError
from app.utils.cog_utils import S3Utils
from app.db.session import get_db
from app.schemas.response import StandardResponse
from app.schemas.validation_artifact_info import (
    ValidationArtifact,
    ValidationArtifactInput,
)
from app.schemas.validation_metric_info import (
    ValidationMetric,
    ValidationMetricInput,
)
from app.services.validation_service import ValidationService
from app.utils.exceptions import OperationException as operation_exception
from app.utils.response_utils import standard_response

router = APIRouter()


@router.post(
    "/validation/metrics",
    response_model=StandardResponse[List[ValidationMetric]],
    status_code=status.HTTP_201_CREATED,
)
async def upload_metrics_details(
    data: ValidationMetricInput, db_app: Session = Depends(get_db)
):
    """
    Upload validation metrics details.

    Args:
        data (ValidationMetricInput): The validation metrics to upload.
        db (Session): The database session.

    Returns:
        StandardResponse[List[ValidationMetric]]: The standard response containing the validation metrics information.
    """

    service = ValidationService(db_app)
    try:
        result = service.upload_metrics_details(data)
        return standard_response(
            status_code=status.HTTP_201_CREATED,
            message="Created new metric details.",
            data=result,
        )
    except operation_exception as exp:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exp))
    except Exception as exp:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal Server Error: {str(exp)}",
        )


@router.get(
    "/validation/metrics", response_model=StandardResponse[List[ValidationMetric]]
)
async def get_metrics_details(
    request: Request,
    db_app: Session = Depends(get_db),
    model_id: Optional[int] = Query(None, gt=0, description="The ID of the model"),
    model_name: str = "",
):
    """
    Retrieve the metrics detals.

    Args:
        :param request: Request
        :param model_id : filter metrics details specific to model_id
        :param model_name : filter metris details specific to model_name
        db (Session): The database session.

    Returns:
        StandardResponse[List[ValidationMetric]]: The standard response containing the validation metrics information.

    """
    service = ValidationService(db_app)
    try:
        data: List[ValidationMetric] = service.get_metrics_details(
            model_pk=model_id, model_name=model_name
        )
        return standard_response(
            status_code=status.HTTP_200_OK,
            message="Validation Metric Details",
            data=data,
            request=request,
        )
    except NoResultFound as exp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exp))
    except operation_exception as exp:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exp))
    except Exception as exp:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal Server Error: {str(exp)}",
        )


@router.get(
    "/validation/artifacts", response_model=StandardResponse[List[ValidationArtifact]]
)
async def get_artifacts_details(
    request: Request,
    db_app: Session = Depends(get_db),
    model_id: Optional[int] = Query(None, gt=0, description="The ID of the model"),
    model_name: str = "",
):
    """
    Retrieve the artifact detals.

    Args:
        :param request: Request
        :param model_id : filter artifact details specific to model_id
        :param model_name : filter artifact details specific to model_name
        :param db_app (Session): The database session.

    Returns:
        StandardResponse[List[ValidationArtifact]]: The standard response containing the validation metrics information.

    """
    service = ValidationService(db_app)
    try:
        data: List[ValidationArtifact] = service.get_artifacts_details(
            model_pk=model_id, model_name=model_name
        )
        return standard_response(
            status_code=status.HTTP_200_OK,
            message="Validation Artifact Details",
            data=data,
            request=request,
        )
    except NoResultFound as exp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exp))
    except operation_exception as exp:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exp))
    except Exception as exp:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal Server Error: {str(exp)}",
        )


@router.post(
    "/validation/artifact",
    response_model=StandardResponse[List[ValidationArtifact]],
    status_code=status.HTTP_201_CREATED,
)
async def upload_validation_artifact(
    data: ValidationArtifactInput, db_app: Session = Depends(get_db)
):
    """
    Upload validation metrics details.

    Args:
        data (ValidationArtifactInput): The validation artifacts to upload.
        db_app (Session): The database session.

    Returns:
        StandardResponse[List[ValidationArtifact]]: The standard response containing
            the validation artifact information.
    """

    service = ValidationService(db_app)
    try:
        result = service.save_validation_artifact(data)
        return standard_response(
            status_code=status.HTTP_201_CREATED,
            message="Validation Artifact Details",
            data=result,
        )
    except operation_exception as exp:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exp))
    except Exception as exp:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal Server Error: {str(exp)}",
        )


@router.get("/s3/get_image")
async def get_image(
    url: str = "",
):
    """
    Given an S3 URL link, return the file for the S3 link as a response.
    """
    try:
        s3_client = S3Utils.create_s3_client()
        bucket, key = split_s3_bucket_key(url)
        file_stream = s3_client.get_object(Bucket=bucket, Key=key)["Body"]

        # Return the file as an attachment in the response
        return StreamingResponse(
            file_stream, headers={"Content-Disposition": f"attachment; filename={key}"}
        )
    except ClientError as exp:
        # Handle errors appropriately
        raise HTTPException(status_code=500, detail=str(exp))
    except Exception as exp:
        raise HTTPException(status_code=500, detail=str(exp))
