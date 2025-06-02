"""
KFP Details schema for the Cognitive Engine API.

This module defines the Pydantic models for KFP Details information,
including the base model and the model with additional fields.

Classes:
    KfpPipelineRunDetailsInput: Base model for kfp pipeline runs input information.
    KfpPipelineRunDetailsBase: Base model for kfp pipeline runs.
    KfpPipelineRunDetails : model extends KfpPipelineRunDetailsBase

Attributes:
    KfpPipelineRunDetailsInput: Base model for kfp pipeline runs input information.
    KfpPipelineRunDetailsBase: Base model for kfp pipeline runs.
    KfpPipelineRunDetails : model extends KfpPipelineRunDetailsBase
"""

from typing import Optional, List, Literal

from pydantic.main import BaseModel

from app.schemas.kfp_experiments import ExperimentBase, Experiment
from app.schemas.kfp_pipeline import PipelineBase, Pipeline
from app.schemas.kfp_run_details import RunDetailsBase, RunDetails
from app.schemas.kfp_tasks_info import TaskBase, Task


class KfpPipelineRunDetailsInput(BaseModel):
    """
    Class that represents  Kfp Pipeline Runs Input details
    """

    run_details: Optional[RunDetailsBase] = None
    experiment_details: Optional[ExperimentBase] = None
    pipeline_details: Optional[PipelineBase] = None
    task_details: Optional[List[TaskBase]] = None
    model_ids: Optional[List[int]] = None


class KfpPipelineRunDetailsBase(BaseModel):
    """
    Class that represents  Kfp Pipeline Runs details
    """

    run_details: Optional[RunDetails] = None
    experiment_details: Optional[Experiment] = None
    pipeline_details: Optional[List[Pipeline]] = None
    task_details: Optional[List[Task]] = None


class KfpPipelineRunDetails(KfpPipelineRunDetailsBase):
    """
    PASS
    """

    class Config:
        """
        orm_mode: True
        """

        orm_mode: Literal[True] = True
        from_attributes: Literal[True] = True
