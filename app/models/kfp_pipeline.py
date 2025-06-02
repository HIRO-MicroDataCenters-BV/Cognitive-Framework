"""
    DB model class for kfp pipeline details
"""

from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Sequence, ForeignKey
from sqlalchemy.orm import relationship
from app.db.session import Base


class Pipeline(Base):
    """
    Represents a pipeline entity.

    Attributes:
        uuid (str): The unique identifier for the pipeline.
        model_id (int): model id associated with the pipeline
        createdAt_in_sec (int): The timestamp when the pipeline was created.
        name (str): name for the pipeline
        description (str): description of the pipeline
        parameters (str): parameters of the pipeline
        status (str): pipeline status
        pipeline_spec (str): specification yaml of pipeline
        pipeline_spec_uri (str): uri of the pipeline specification
    """

    __tablename__ = "pipelines"
    id = Column(Integer, Sequence("model_info_id_seq"), primary_key=True)
    uuid = Column(String(255))
    model_id = Column(Integer, ForeignKey("model_info.id"))
    createdAt_in_sec = Column(DateTime, default=datetime.utcnow, nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(String(255), nullable=False)
    parameters = Column(String)
    status = Column(String(255))
    experiment_uuid = Column(
        String(255), ForeignKey("experiments.uuid"), nullable=False
    )
    pipeline_spec = Column(String)
    pipeline_spec_uri = Column(String)
    experiments = relationship("Experiment", back_populates="pipelines")
    pipeline_details = relationship("ModelInfo", back_populates="model_pipelines")
