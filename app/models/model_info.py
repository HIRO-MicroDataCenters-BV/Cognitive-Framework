"""
    DB model class for ModelInfo
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Sequence
from sqlalchemy.orm import relationship
from app.db.session import Base


class ModelInfo(Base):
    """
    The following attributes of a model_info are stored in this table:
           * id - id
           * name - name of the model
           * register_date - date of registering the model
           * type - type  of the model
           * last_modified_time - last modified time of the model
           * last_modified_user_id - last modified user id of the model
    """

    __tablename__ = "model_info"
    id = Column(Integer, Sequence("model_info_id_seq"), primary_key=True)
    name = Column(String)
    version = Column(Integer)
    register_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    register_user_id = Column(Integer)
    type = Column(String)
    description = Column(String)
    last_modified_time = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_modified_user_id = Column(Integer)

    # Define the one-to-many relationship with ModelDataset
    model_info_datasets = relationship(
        "ModelDataset",
        back_populates="model_info",
        foreign_keys="[ModelDataset.model_id]",
        cascade="all, delete",
    )
    # Define the one-to-many relationship with ModelFileUpload
    model_uploads = relationship(
        "ModelFileUpload",
        back_populates="model_info",
        foreign_keys="[ModelFileUpload.model_id]",
        cascade="all, delete",
    )

    # Define the relationship with ModelValidationMetric
    model_validation_metrics = relationship(
        "ValidationMetric",
        foreign_keys="[ValidationMetric.model_id]",
        back_populates="model_info_metrics",
        cascade="all, delete",
    )

    # Define the relationship with ModelValidationArtifact
    model_validation_artifacts = relationship(
        "ValidationArtifact",
        back_populates="model_info_artifacts",
        foreign_keys="[ValidationArtifact.model_id]",
        cascade="all, delete",
    )

    # Define the relationship with KfpPipelines
    model_pipelines = relationship(
        "Pipeline",
        back_populates="pipeline_details",
        foreign_keys="[Pipeline.model_id]",
        cascade="all, delete",
    )
