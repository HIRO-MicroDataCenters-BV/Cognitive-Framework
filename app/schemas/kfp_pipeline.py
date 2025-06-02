"""
KFP Pipeline schema for the Cognitive Engine API.

This module defines the Pydantic models for KFP pipeline information,
including the base model and the model with additional fields.

Classes:
    PipelineBase: Base model for pipeline information.
    Pipeline: Model for pipeline information with additional fields.

Attributes:
    PipelineBase: Base model for pipeline information.
    Pipeline: Model for pipeline information with additional fields.
"""

from datetime import datetime
from typing import Optional, Literal, List, Any
from pydantic import BaseModel, Field

from app.schemas.kfp_run_details import RunDetails


class PipelineRuns(BaseModel):
    """
    Class that represents  pipeline runs
    """

    pipeline_id: str
    versions: Any
    runs: Optional[List[RunDetails]]

    class Config:
        """
        Config class for standard response
        """

        # This setting ensures that fields with value None are excluded from the output
        exclude_none = True
        orm_mode: Literal[True] = True
        from_attributes: Literal[True] = True


class PipelineBase(BaseModel):
    """
    Class that represents  pipeline details
    """

    uuid: str
    model_id: Optional[int] = None
    name: str
    description: str
    parameters: Optional[str] = None
    status: Optional[str] = None
    createdAt_in_sec: datetime
    experiment_uuid: str
    pipeline_spec: Optional[str] = None
    pipeline_spec_uri: Optional[str] = None


class PipelineDetails(BaseModel):
    """
    Class that represents pipeline details related to model
    """

    uuid: str
    name: str
    description: Optional[str] = None
    createdAt_in_sec: datetime = Field(alias="created_at")

    class Config:
        """
        orm_mode: True

        """

        orm_mode: Literal[True] = True
        from_attributes: Literal[True] = True
        allow_population_by_field_name = True


class Pipeline(PipelineBase):
    """
    Class that represents  pipeline details
    """

    id: int

    class Config:
        """
        orm_mode: True

        """

        orm_mode: Literal[True] = True
        from_attributes: Literal[True] = True


class InferenceLogs(BaseModel):
    """
    Class that represents  Inference Logs
    """

    logs: Optional[Any]

    class Config:
        """
        Config class for standard response
        """

        # This setting ensures that fields with value None are excluded from the output
        exclude_none = True
        orm_mode: Literal[True] = True
        from_attributes: Literal[True] = True


class PodLogResponse(BaseModel):
    """
    Schema for pod logs response.
    """

    pod_name: str
    namespace: Optional[str]
    container_name: Optional[str]
    pod_logs: List[str]

    class Config:
        """
        Config class for standard response
        """

        # This setting ensures that fields with value None are excluded from the output
        exclude_none = True
        orm_mode: Literal[True] = True
        from_attributes: Literal[True] = True


class PodEventResponse(BaseModel):
    """
    Schema for pod events response.
    """

    pod_name: str
    namespace: Optional[str]
    pod_events: List[str]

    class Config:
        """
        Config class for standard response
        """

        # This setting ensures that fields with value None are excluded from the output
        exclude_none = True
        orm_mode: Literal[True] = True
        from_attributes: Literal[True] = True


class PodDefinitionResponse(BaseModel):
    """
    Schema for pod definition response.
    """

    pod_name: str
    namespace: Optional[str]
    pod_definition: List[str]

    class Config:
        """
        Config class for standard response
        """

        # This setting ensures that fields with value None are excluded from the output
        exclude_none = True
        orm_mode: Literal[True] = True
        from_attributes: Literal[True] = True


class DeploymentsResponse(BaseModel):
    """
    Schema for deployments response.
    """

    namespace: Optional[str]
    deployments: List[str]

    class Config:
        """
        Config class for standard response
        """

        # This setting ensures that fields with value None are excluded from the output
        exclude_none = True
        orm_mode: Literal[True] = True
        from_attributes: Literal[True] = True
