"""
    This module defines the Pydantic models for the Component entity.
"""
from typing import List, Dict, Any, Optional

from pydantic import BaseModel


class ComponentCreate(BaseModel):
    """
    Class that represents component creation details.
    """

    name: str
    input_path: List[Dict[str, Any]]
    output_path: List[Dict[str, Any]]
    component_file: Optional[str] = None


class ComponentResponse(BaseModel):
    """
    Class that represents component response details.
    """

    id: int
    name: str
    input_path: List[Dict[str, Any]]
    output_path: List[Dict[str, Any]]
    component_file: Optional[str] = None

    class Config:
        """
        orm_mode: True
        """

        orm_mode = True
