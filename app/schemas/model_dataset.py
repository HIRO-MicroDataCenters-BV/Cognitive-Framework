"""
Model Dataset schema for the Cognitive Engine API.

This module defines the Pydantic models for model dataset information,
including the base model and the model with additional fields.

Classes:
    ModelDatasetBase: Base model for model dataset information.
    ModelDataset: Model for model dataset information with additional fields.

Attributes:
    ModelDatasetBase: Base model for model dataset information.
    ModelDataset: Model for model dataset information with additional fields.
"""

from datetime import datetime
from typing import Literal, Optional, List

from pydantic import BaseModel

from app.schemas.dataset_info import DatasetInfoDetails

# from app.schemas.kfp_experiments import ExperimentDetails
# from app.schemas.kfp_pipeline import PipelineDetails
# from app.schemas.kfp_run_details import RunDetail
from app.schemas.model_upload import ModelFileUploadDetails

# from app.schemas.validation_artifact_info import ValidationArtifactDetails
# from app.schemas.validation_metric_info import ValidationMetricDetails


class ModelDatasetBase(BaseModel):
    """
    Class that represents  model dataset details
    """

    user_id: int
    model_id: int
    dataset_id: int
    linked_time: datetime


class ModelDetailedResponse(BaseModel):
    """
    class defining detailed model response fields
    """

    model_id: int
    model_name: str
    model_description: Optional[str] = None
    author: int
    register_date: datetime
    datasets: List[DatasetInfoDetails]
    model_files: List[ModelFileUploadDetails]
    # validation_metrics: List[ValidationMetricDetails]
    # validation_artifacts: List[ValidationArtifactDetails]
    # pipelines: List[PipelineDetails]
    # experiments: List[ExperimentDetails]
    # run_details: List[RunDetail]

    class Config:
        """
        orm_mode: True
        """

        orm_mode: Literal[True] = True
        from_attributes: Literal[True] = True


class ModelDataset(ModelDatasetBase):
    """
    Class that represents  model dataset details
    """

    id: int

    class Config:
        """
        orm_mode: True
        """

        orm_mode: Literal[True] = True
        from_attributes: Literal[True] = True
