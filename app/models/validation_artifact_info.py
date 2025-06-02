"""
    DB model class for validation artifact details
"""

from sqlalchemy import Column, Integer, Sequence, ForeignKey, JSON, UniqueConstraint
from sqlalchemy.orm import relationship
from app.db.session import Base


class ValidationArtifact(Base):
    """
    The following attributes of a validation_artifact are stored in this table:
    * id - id
    * model_id - id of the model
    * dataset_id - id of the dataset
    * validation_artifacts - JSON field for various validation artifacts
    """

    __tablename__ = "validation_artifact"
    id = Column(
        Integer(),
        Sequence("validation_artifact_id_seq"),
        primary_key=True,
        autoincrement=True,
    )
    model_id = Column(Integer(), ForeignKey("model_info.id"))
    dataset_id = Column(Integer(), ForeignKey("dataset_info.id"))
    validation_artifacts = Column(JSON, nullable=True)
    dataset_info_artifacts = relationship(
        "DatasetInfo", back_populates="dataset_validation_artifacts"
    )
    model_info_artifacts = relationship(
        "ModelInfo", back_populates="model_validation_artifacts"
    )
    __table_args__ = (
        UniqueConstraint("model_id", "dataset_id", name="unique_model_id_dataset_id"),
    )

    def to_dict(self):
        """
            create dict from object
        :return: dict object
        """
        return {
            "id": self.id,
            "model_id": self.model_id,
            "dataset_id": self.dataset_id,
            "validation_artifacts": self.validation_artifacts or {},
        }
