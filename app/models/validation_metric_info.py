"""
    DB model class for validation metric details
"""

from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    Sequence,
    Float,
    DateTime,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from app.db.session import Base


class ValidationMetric(Base):
    """
    The following attributes of a validation_metric are stored in this table:
           * id - id
           * model_id - id of the model
           * dataset_id - id of the dataset
           * accuracy_score - accuracy score validation metric
           * example_count - example_count validation metric
           * f1_score- f1_score validation metric
           * log_loss- log_loss validation metric
           * precision_score - precision_score validation metric
           * recall_score - recall_score validation metric
           * roc_auc - roc_auc validation metric
           * score - score validation metric
           * cpu_consumption - cpu_consumption metric
           * memory_utilization - memory_utilization metric
    """

    __tablename__ = "validation_metric"
    id = Column(Integer, Sequence("validation_metric_id_seq"), primary_key=True)
    model_id = Column(Integer, ForeignKey("model_info.id"))
    dataset_id = Column(Integer, ForeignKey("dataset_info.id"))
    registered_date_time = Column(DateTime, default=datetime.utcnow, nullable=False)
    accuracy_score = Column(Float)
    example_count = Column(Integer)
    f1_score = Column(Float)
    log_loss = Column(Float)
    precision_score = Column(Float)
    recall_score = Column(Float)
    roc_auc = Column(Integer)
    score = Column(Float)
    cpu_consumption = Column(Float)
    memory_utilization = Column(Float)
    # define relationship between dataset_info and validation_metric
    dataset_info_metrics = relationship(
        "DatasetInfo", back_populates="dataset_validation_metrics"
    )
    # define relationship between model_info and validation_metric
    model_info_metrics = relationship(
        "ModelInfo", back_populates="model_validation_metrics"
    )
    __table_args__ = (
        UniqueConstraint(
            "model_id", "dataset_id", name="unique_model_id_dataset_id_per_metric"
        ),
    )
