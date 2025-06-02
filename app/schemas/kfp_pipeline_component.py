"""
KFP Pipeline Component schema for the Cognitive Engine API.

This module defines the Pydantic models for KFP pipeline Component information,
including the base model and the model with additional fields.

"""

from typing import List, Optional, Dict
from pydantic import BaseModel, Field


class Input(BaseModel):
    """
    Class that represents  Inputs in pipeline component
    """

    name: str
    value: str


class Artifact(BaseModel):
    """
    Class that represents  Artifact in pipeline component
    """

    name: str
    path: str
    s3: Optional[
        Dict[str, str]
    ] = None  # s3 key can be optional as it is not in all responses.
    optional: Optional[bool]


class Output(BaseModel):
    """
    Class that represents  Output in pipeline component
    """

    artifacts: Optional[List[Artifact]] = []
    exitCode: Optional[str]


class ResourceDuration(BaseModel):
    """
    Class that represents  ResourceDuration in pipeline component
    """

    cpu: Optional[int]
    memory: Optional[int]


class Child(BaseModel):
    """
    Class that represents  Children in pipeline component
    """

    id: str
    podName: Optional[str]
    name: str
    inputs: Optional[List[Input]] = []
    outputs: Optional[Output]
    status: str
    startedAt: str
    finishedAt: str
    resourcesDuration: Optional[ResourceDuration]
    children: Optional[List["Child"]] = []  # Self-referential children
    run_id: Optional[str]


class TaskStructure(BaseModel):
    """
    Class that represents  TaskStructure in pipeline component
    """

    id: str
    podName: Optional[str]
    name: str
    inputs: List[Input]
    outputs: List[str] = []
    status: str
    startedAt: str
    finishedAt: str
    resourcesDuration: ResourceDuration
    children: List[Child]


class PipelineComponent(BaseModel):
    """
    Class that represents  pipeline component
    """

    _run_id: Optional[str] = Field(alias="run_id")
    pipeline_workflow_name: str
    task_structure: Dict[str, TaskStructure]  # Dictionary of task structures


class PipelineResponse(BaseModel):
    """
    Class that represents  collections of pipeline component
    """

    __root__: List[PipelineComponent]  # To match the list of pipelines
