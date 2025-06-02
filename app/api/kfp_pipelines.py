"""
API endpoints for managing validation metrics and artifacts.

This module provides endpoints for operations on validation metrics and artifacts.
"""

import urllib.parse
from typing import List, Optional

from fastapi import APIRouter, HTTPException, status
from fastapi.params import Depends
from sqlalchemy.orm import Session
import cogflow
from app.db.session import get_db
from app.schemas.kfp_details import KfpPipelineRunDetails, KfpPipelineRunDetailsInput
from app.schemas.kfp_pipeline import (
    Pipeline,
    PipelineRuns,
    InferenceLogs,
    PodLogResponse,
    PodEventResponse,
    PodDefinitionResponse,
    DeploymentsResponse,
)
from app.schemas.kfp_pipeline_component import (
    PipelineResponse,
    PipelineComponent,
    Child,
)
from app.schemas.kfp_run_details import RunDetails, PipelineRunOutput

from app.schemas.response import StandardResponse
from app.services.kfp_pipeline_service import KfpPipelineService
from app.utils.response_utils import standard_response
from app.utils.exceptions import (
    OperationException as operation_exception,
    NoResultFound,
    InvalidValueException,
)

router = APIRouter()


@router.post(
    "/pipeline",
    response_model=StandardResponse[KfpPipelineRunDetails],
    status_code=status.HTTP_201_CREATED,
)
async def post_pipeline_details(
    data: KfpPipelineRunDetailsInput, db_app: Session = Depends(get_db)
):
    """
    Endpoint to add pipeline details.

    This endpoint expects a JSON payload with the pipeline details
    and uses the KfpPipelineService to upload these details.

    Returns:
        Response: JSON response containing the uploaded pipeline details.
    """
    try:
        service = KfpPipelineService(db_app)
        result = service.upload_pipeline_details(data)
        return standard_response(
            status_code=status.HTTP_201_CREATED,
            message="Created new Pipeline details",
            data=result,
        )
    except operation_exception as exp:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exp))
    except Exception as exp:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal Server Error: {str(exp)}",
        )


@router.get("/pipeline/{model_id}", response_model=StandardResponse[List[Pipeline]])
async def get_pipeline_by_model_id(model_id: int, db_app: Session = Depends(get_db)):
    """
    Endpoint to retrieve pipeline details by model ID.

    Args:
        model_id (int): ID of the model to fetch pipeline details for.
        db_app: db session

    Returns:
        Response: JSON response containing the pipeline details if found,
                  otherwise a 400 error message.
    """
    try:
        service = KfpPipelineService(db_app)
        result = service.get_pipeline_by_model_id(model_id=model_id)
        return standard_response(
            status_code=status.HTTP_200_OK, message="Pipeline Details", data=result
        )
    except operation_exception as exp:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exp))
    except Exception as exp:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal Server Error: {str(exp)}",
        )


@router.get(
    "/pipeline/runs/{pipeline_id}", response_model=StandardResponse[List[RunDetails]]
)
async def get_run_details_by_pipeline_id(
    pipeline_id: str, db_app: Session = Depends(get_db)
):
    """
    Endpoint to retrieve run details by pipeline ID.

    Args:
        pipeline_id (int): ID of the pipeline.
        db_app : db session

    Returns:
        Response: JSON response containing the pipeline run details if found,
                  otherwise a 400 error message.
    """
    try:
        service = KfpPipelineService(db_app)
        result = service.list_runs_by_pipeline_id(pipeline_id=pipeline_id)
        return standard_response(
            status_code=status.HTTP_200_OK, message="Run Details", data=result
        )
    except operation_exception as exp:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exp))
    except Exception as exp:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal Server Error: {str(exp)}",
        )


@router.delete(
    "/pipeline/runs/{pipeline_id}", response_model=StandardResponse[List[RunDetails]]
)
async def delete_run_details_by_pipeline_id(
    pipeline_id: str, db_app: Session = Depends(get_db)
):
    """
    Endpoint to delete pipeline details by pipeline ID.

    Args:
        pipeline_id (int): ID of the pipeline.

    Returns:
        Response: Str returning the successful deleted message,
                  otherwise a 400 error message.
    """
    try:
        service = KfpPipelineService(db_app)
        data = service.delete_runs_by_pipeline_id(pipeline_id=pipeline_id)
        return standard_response(
            status_code=status.HTTP_200_OK,
            message="Run details deleted successfully",
            data=data,
        )
    except operation_exception as exp:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exp))
    except Exception as exp:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal Server Error: {str(exp)}",
        )


@router.delete(
    "/pipeline/{pipeline_id}", response_model=StandardResponse[List[Pipeline]]
)
async def delete_pipeline_by_pipeline_id(
    pipeline_id: str, db_app: Session = Depends(get_db)
):
    """
    Endpoint to delete pipeline details.

    This endpoint delete the pipeline details based on pipeline_id.

    Returns:
        Response: StandardResponse[List[Pipeline]]
    """
    try:
        service = KfpPipelineService(db_app)
        data = service.delete_pipeline_details(pipeline_id=pipeline_id)
        return standard_response(
            status_code=status.HTTP_200_OK,
            message="Pipeline details deleted successfully",
            data=data,
        )
    except operation_exception as exp:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exp))
    except Exception as exp:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal Server Error: {str(exp)}",
        )


@router.get("/pipelines", response_model=StandardResponse[PipelineRuns])
async def list_pipelines_by_name(pipeline_name: str, db_app: Session = Depends(get_db)):
    """
    Endpoint to list out the pipeline details.

    This endpoint list out the pipeline details based on pipeline_name.

    Returns:
        Response: .StandardResponse[PipelineRuns]
    """
    if not pipeline_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="pipeline_name is required"
        )
    try:
        decoded_pipeline_name = urllib.parse.unquote(pipeline_name)
        service = KfpPipelineService(db_app)
        pipeline_exists = service.check_pipeline_exists(decoded_pipeline_name)
        if not pipeline_exists:
            raise NoResultFound(
                message=f"pipeline with name '{decoded_pipeline_name}' not exists"
            )
        data = cogflow.list_pipelines_by_name(decoded_pipeline_name)

        if not data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="No Pipeline details found",
            )
        result = PipelineRuns(**data)
        return standard_response(
            status_code=status.HTTP_200_OK, message="Pipeline details ", data=result
        )
    except NoResultFound as exp:
        raise HTTPException(status_code=404, detail=str(exp))
    except Exception as exp:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal Server Error: {str(exp)}",
        )


@router.get("/inferenceservice/logs", response_model=StandardResponse[InferenceLogs])
async def get_inference_logs_by_service_name(
    inference_service_name: str,
    namespace: Optional[str] = None,
    container_name: Optional[str] = None,
):
    """
    Endpoint to get the inference service_log details.

    This endpoint get the inference service_log details based on service_name.

    Returns:
        Response: .StandardResponse[InferenceLogs]

    """
    try:
        if not inference_service_name:
            error_message = "Missing required parameters: 'inference_service_name' "
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Internal Server Error: {error_message}",
            )
        data = cogflow.NotebookPlugin().get_inference_service_logs(
            inference_service_name=inference_service_name,
            namespace=namespace,
            container_name=container_name,
        )

        if not data:
            error_message = "No logs found or an error occurred while fetching logs."
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Internal Server Error: {error_message}",
            )
        result = InferenceLogs(**data)
        return standard_response(
            status_code=status.HTTP_204_NO_CONTENT,
            message="Inference Logs",
            data=result,
        )
    except Exception as exp:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal Server Error: {str(exp)}",
        )


@router.get(
    "/pipelines/component",
    response_model=StandardResponse[PipelineResponse],
)
async def get_pipeline_component_by_pipeline(
    pipeline_id: Optional[str] = None,
    pipeline_name: Optional[str] = None,
    pipeline_workflow_name: Optional[str] = None,
):
    """
        retrieve pipeline component details for the given pipeline_id or pipeline_name
    :param pipeline_id:
    :param pipeline_name:
    :param pipeline_workflow_name:
    :return:
    """
    try:
        if not pipeline_id and not pipeline_name and not pipeline_workflow_name:
            raise InvalidValueException(
                "Invalid Input :Pipeline_id or Pipeline_name or pipeline_workflow_name should not be empty"
            )
        if pipeline_id is not None:
            data = cogflow.get_pipeline_task_sequence_by_pipeline_id(pipeline_id)
        elif pipeline_name is not None:
            data = cogflow.get_pipeline_task_sequence(pipeline_name=pipeline_name)
        else:
            data = cogflow.get_pipeline_task_sequence(
                pipeline_workflow_name=pipeline_workflow_name
            )
        return standard_response(
            status_code=200, message="pipeline component details", data=data
        )
    except InvalidValueException as exp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=exp.message,
        )
    except ValueError as exp:
        raise HTTPException(status_code=404, detail=str(exp))
    except Exception as exp:
        raise HTTPException(
            status_code=500, detail=f"Internal Server Error: {str(exp)}"
        )


@router.get(
    "/pipelines/component/run",
    response_model=StandardResponse[PipelineComponent],
)
async def get_pipeline_component_by_run(
    run_id: Optional[str] = None, run_name: Optional[str] = None
):
    """
        retrieve pipeline component details for the given run_id or run_name
    :param run_name:
    :param run_id:
    :return:
    """
    try:
        if not run_id and not run_name:
            raise InvalidValueException(
                "Invalid Input :run_id or run_name should not be empty"
            )
        if run_id is not None:
            (
                pipeline_workflow_name,
                task_structure,
            ) = cogflow.get_pipeline_task_sequence_by_run_id(run_id)
        else:
            (
                pipeline_workflow_name,
                task_structure,
            ) = cogflow.get_pipeline_task_sequence_by_run_name(run_name)

        data = {
            "pipeline_workflow_name": pipeline_workflow_name,
            "task_structure": task_structure,
        }
        return standard_response(
            status_code=200, message="pipeline component details", data=data
        )
    except InvalidValueException as exp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=exp.message,
        )
    except ValueError as exp:
        raise HTTPException(status_code=404, detail=str(exp))
    except Exception as exp:
        raise HTTPException(
            status_code=500, detail=f"Internal Server Error: {str(exp)}"
        )


@router.get("/pipelines/task", response_model=StandardResponse[List[Child]])
async def get_pipeline_task(
    task_id: str, run_id: Optional[str] = None, run_name: Optional[str] = None
):
    """
        retrieve pipeline component details for the given task_id,run_id,run_name
    :param task_id:
    :param run_id:
    :param run_name:
    :return:
    """
    if not task_id:
        raise HTTPException(status_code=400, detail="task_id is required")
    try:
        data = cogflow.get_task_structure_by_task_id(task_id, run_id, run_name)
        return standard_response(
            status_code=200, message="pipeline component details", data=data
        )
    except ValueError as exp:
        raise HTTPException(status_code=404, detail=str(exp))
    except Exception as exp:
        raise HTTPException(
            status_code=500, detail=f"Internal Server Error: {str(exp)}"
        )


@router.get("/pipelines/runs", response_model=StandardResponse[PipelineRunOutput])
async def get_pipeline_runs():
    """
    retrieve pipeline runs details

    """
    try:
        data = cogflow.NotebookPlugin().list_all_kfp_runs()
        return standard_response(
            status_code=200, message="pipeline runs details", data=data
        )
    except ValueError as exp:
        raise HTTPException(status_code=404, detail=str(exp))
    except Exception as exp:
        raise HTTPException(
            status_code=500, detail=f"Internal Server Error: {str(exp)}"
        )


@router.get("/pod/logs", response_model=StandardResponse[PodLogResponse])
async def get_pod_logs(
    pod_name: str,
    namespace: Optional[str] = None,
    container_name: Optional[str] = None,
):
    """
    Retrieve the logs of a specified pod.

    :param pod_name: The name of the pod.
    :param namespace: The namespace of the pod (optional, defaults to the plugin default).
    :param container_name: The name of the container within the pod (optional).
    :return: JSON-formatted logs of the specified pod.
    """
    if not pod_name:
        raise HTTPException(status_code=400, detail="pod_name is required")

    try:
        data = cogflow.NotebookPlugin().get_pod_logs(
            pod_name=pod_name, namespace=namespace, container_name=container_name
        )
        result = {
            "pod_name": pod_name,
            "namespace": namespace,
            "container_name": container_name,
            "pod_logs": data,
        }

        return standard_response(
            status_code=200, message="Pod logs details", data=result
        )
    except Exception as exp:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve pod logs: {str(exp)}"
        )


@router.get("/pod/events", response_model=StandardResponse[PodEventResponse])
async def get_pod_events(pod_name: str, namespace: Optional[str] = None):
    """
    Retrieve the events of a specified pod.

    :param pod_name: The name of the pod.
    :param namespace: The namespace of the pod (optional, defaults to the plugin default).
    :return: JSON-formatted events of the specified pod.
    """
    if not pod_name:
        raise HTTPException(status_code=400, detail="pod_name is required")

    try:
        data = cogflow.NotebookPlugin().get_pod_events(
            podname=pod_name, namespace=namespace
        )
        result = {
            "pod_name": pod_name,
            "namespace": namespace,
            "pod_events": data,
        }

        return standard_response(
            status_code=200, message="Pod events details", data=result
        )
    except Exception as exp:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve pod events: {str(exp)}"
        )


@router.get("/pod/definition", response_model=StandardResponse[PodDefinitionResponse])
async def get_pod_definition(pod_name: str, namespace: Optional[str] = None):
    """
    Retrieve the definition of a specified pod.

    :param pod_name: The name of the pod.
    :param namespace: The namespace of the pod (optional, defaults to the plugin default).
    :return: JSON-formatted definition of the specified pod.
    """
    if not pod_name:
        raise HTTPException(status_code=400, detail="pod_name is required")

    try:
        data = cogflow.NotebookPlugin().get_pod_definition(
            podname=pod_name, namespace=namespace
        )
        result = {
            "pod_name": pod_name,
            "namespace": namespace,
            "pod_definition": data,
        }

        return standard_response(
            status_code=200, message="Pod definition details", data=result
        )
    except Exception as exp:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve pod definition: {str(exp)}"
        )


@router.get("/deployments", response_model=StandardResponse[DeploymentsResponse])
async def get_deployments(namespace: Optional[str] = None):
    """
    Retrieve the deployments of specified namespace.

    :param namespace: The namespace of the pod (optional, defaults to the plugin default).
    :return: JSON-formatted deployments of the specified namespace.
    """

    try:
        data = cogflow.get_deployments(namespace=namespace)
        result = {
            "namespace": namespace,
            "deployments": data,
        }

        return standard_response(
            status_code=200, message="Deployments details", data=result
        )
    except Exception as exp:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve deployments: {str(exp)}"
        )
