"""
Pipeline Components API
"""
from fastapi import Depends, APIRouter, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.db.session import get_db
from app.models.pipeline_component import PipelineComponent
from app.utils.response_utils import standard_response
from app.schemas.pipeline_components import (
    PipelineComponentCreate,
    PipelineComponentResponse,
)

router = APIRouter()


@router.post("/pipeline-components", response_model=PipelineComponentResponse)
def create_pipeline_component(
    pipeline_component: PipelineComponentCreate, db_session: Session = Depends(get_db)
):
    """
    Create a new pipeline component.
    Args:
        pipeline_component (PipelineComponentCreate): The pipeline component to create.
        db_session (Session): The database session.
    Returns:
        PipelineComponentResponse: The created pipeline component.
    """
    try:
        new_pipeline_component = PipelineComponent(
            name=pipeline_component.name,
            pipeline_components=pipeline_component.pipeline_components,
            input_path=pipeline_component.input_path,
            output_path=pipeline_component.output_path,
        )
        db_session.add(new_pipeline_component)
        db_session.commit()
        db_session.refresh(new_pipeline_component)
        return standard_response(
            status_code=status.HTTP_201_CREATED,
            message="Pipeline component created successfully.",
            data=new_pipeline_component,
        )
    except IntegrityError as exp:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "message": "Pipeline component already exists.",
                "detail": str(exp.orig),
            },
        )
    except Exception as exp:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal Exception: {str(exp)}",
        )


@router.get("/pipeline-components", response_model=list[PipelineComponentResponse])
def get_pipeline_components(db_session: Session = Depends(get_db)):
    """
    Retrieve all pipeline components.
    Args:
        db_session (Session): The database session.
    Returns:
        list[PipelineComponentResponse]: List of pipeline components.
    """
    try:
        pipeline_components = db_session.query(PipelineComponent).all()
        return standard_response(
            status_code=status.HTTP_200_OK,
            message="Pipeline components retrieved successfully.",
            data=pipeline_components,
        )
    except Exception as exp:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal Exception: {str(exp)}",
        )


@router.delete(
    "/pipeline-components/{pipeline_component_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_pipeline_component(
    pipeline_component_id: int, db_session: Session = Depends(get_db)
):
    """
    Delete a pipeline component by ID.
    Args:
        pipeline_component_id (int): The ID of the pipeline component to delete.
        db_session (Session): The database session.
    Returns:
        None
    """
    try:
        pipeline_component = (
            db_session.query(PipelineComponent)
            .filter(PipelineComponent.id == pipeline_component_id)
            .first()
        )
        if not pipeline_component:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Pipeline component with ID {pipeline_component_id} not found.",
            )
        db_session.delete(pipeline_component)
        db_session.commit()
    except Exception as exp:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal Exception: {str(exp)}",
        )
