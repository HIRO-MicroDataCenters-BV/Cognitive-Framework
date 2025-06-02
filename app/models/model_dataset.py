"""
    DB model class for ModelDataset relation
"""

from datetime import datetime
from sqlalchemy import Column, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.db.session import Base


class ModelDataset(Base):
    """
    Represents the relationship between models and datasets.

    Attributes:
        id (int): The unique identifier for the model-dataset link.
        user_id (int): The ID of the user associated with the link.
        model_id (int): The ID of the model associated with the link.
        dataset_id (int): The ID of the dataset associated with the link.
        linked_time (datetime): The timestamp when the link was created.
    """

    __tablename__ = "model_dataset"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    model_id = Column(
        Integer, ForeignKey("model_info.id", ondelete="CASCADE"), nullable=False
    )
    dataset_id = Column(
        Integer, ForeignKey("dataset_info.id", ondelete="CASCADE"), nullable=False
    )
    linked_time = Column(DateTime, nullable=False, default=datetime.now)
    model_info = relationship("ModelInfo", back_populates="model_info_datasets")
    dataset_info = relationship("DatasetInfo", back_populates="model_datasets")
