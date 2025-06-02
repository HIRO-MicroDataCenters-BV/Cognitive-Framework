"""
    DB model class for DatasetInfo
"""

from datetime import datetime
from sqlalchemy import Column, Integer, DateTime, CheckConstraint, String
from sqlalchemy.orm import relationship

from app.db.session import Base


class DatasetInfo(Base):
    """
    Class that represents dataset details.
    The following attributes of a dataset_info are stored in this table:
    * id - id of the dataset
    * train_and_inference_type - type of dataset i.e traindata or inferencedata or both
    * data_source_type - source type of dataset i.e upload or table or broker select
    * dataset_name - name of the dataset
    * user_id - user id who registered the dataset
    * register_date_time - date of registering the dataset
    * last_modified_time - last modified time of the dataset
    * last_modified_user_id - last modified user id of the dataset
    * filepath - file path of the dataset
    * filename - file name of the dataset
    """

    __tablename__ = "dataset_info"
    id = Column(Integer, primary_key=True, index=True)
    train_and_inference_type = Column(
        Integer, CheckConstraint("train_and_inference_type IN (0, 1, 2)")
    )
    data_source_type = Column(Integer, CheckConstraint("data_source_type IN (0, 1 ,2)"))
    dataset_name = Column(String)
    description = Column(String)
    user_id = Column(Integer)
    register_date_time = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_modified_time = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_modified_user_id = Column(Integer)
    dataset_uploads = relationship(
        "DatasetFileDetails", back_populates="dataset_info", cascade="all, delete"
    )
    dataset_table_registraters = relationship(
        "DatasetTableDetails", back_populates="dataset_info", cascade="all, delete"
    )
    dataset_validation_metrics = relationship(
        "ValidationMetric",
        foreign_keys="ValidationMetric.dataset_id",
        back_populates="dataset_info_metrics",
        cascade="all, delete",
    )
    dataset_validation_artifacts = relationship(
        "ValidationArtifact",
        back_populates="dataset_info_artifacts",
        cascade="all, delete",
    )
    model_datasets = relationship(
        "ModelDataset",
        back_populates="dataset_info",
        foreign_keys="ModelDataset.dataset_id",
        cascade="all, delete",
    )

    dataset_topic_mapping = relationship(
        "DatasetTopicDetails", back_populates="dataset_topic", cascade="all, delete"
    )
