"""
Schema for pipeline components.
"""
from typing import Any, Dict, List
from pydantic import BaseModel


class PipelineComponentCreate(BaseModel):
    """
    Class that represents pipeline component creation details.
    """

    name: str
    pipeline_components: Dict[str, Any]
    input_path: List[Dict[str, Any]]
    output_path: List[Dict[str, Any]]


class PipelineComponentResponse(BaseModel):
    """
    Class that represents pipeline component response details.
    """

    id: int
    name: str
    pipeline_components: Dict[str, Any]
    input_path: List[Dict[str, Any]]
    output_path: List[Dict[str, Any]]

    class Config:
        """
        orm_mode: True
        """

        orm_mode = True
