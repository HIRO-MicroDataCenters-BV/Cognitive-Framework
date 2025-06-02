"""
Component API
"""
from fastapi import Depends, APIRouter, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.component import Component
from app.utils.response_utils import standard_response
from app.schemas.component import ComponentCreate, ComponentResponse

router = APIRouter()


@router.post("/components", response_model=ComponentResponse)
def create_component(component: ComponentCreate, db_session: Session = Depends(get_db)):
    """
    Create a new component.
    Args:
        component (ComponentCreate): The component to create.
        db_session (Session): The database session.
    Returns:
        ComponentResponse: The created component.
    """
    try:
        new_component = Component(
            name=component.name,
            input_path=component.input_path,
            output_path=component.output_path,
            component_file=component.component_file,
        )
        db_session.add(new_component)
        db_session.commit()
        db_session.refresh(new_component)
        return new_component
    except IntegrityError as exp:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "message": "Component already exists.",
                "detail": str(exp.orig),
            },
        )
    except Exception as exp:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal Exception: {str(exp)}",
        )


@router.get("/components", response_model=list[ComponentResponse])
def get_components(db_session: Session = Depends(get_db)):
    """
    Retrieve all components.
    Args:
        db_session (Session): The database session.
    Returns:
        list[ComponentResponse]: A list of components.
    """
    try:
        components = db_session.query(Component).all()
        return standard_response(
            status_code=status.HTTP_200_OK,
            message="Components retrieved successfully.",
            data=components,
        )
    except Exception as exp:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal Exception: {str(exp)}",
        )


@router.delete("/components/{component_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_component(component_id: int, db_session: Session = Depends(get_db)):
    """
    Delete a component by ID.
    Args:
        component_id (int): The ID of the component to delete.
        db_session (Session): The database session.
    Returns:
        None
    """
    try:
        component = (
            db_session.query(Component).filter(Component.id == component_id).first()
        )
        if not component:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Component with ID {component_id} not found.",
            )
        db_session.delete(component)
        db_session.commit()
    except Exception as exp:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal Exception: {str(exp)}",
        )
