"""
    DB model class for model file upload details
"""

from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    Sequence,
    CheckConstraint,
)
from sqlalchemy.orm import relationship
from app.db.session import Base


class ModelFileUpload(Base):
    """
    Class that represents model file upload information
    The following attributes of a model_upload are stored in this table:
    * id - id of the model upload file
    * model_id - model id of the upload file
    * user_id - user who registered the model file
    * register_date - date of registering the model file
    * file_name - file name of the model file
    * file_path - file path of the model file
    * file_type - type of the model file
    * file_description - description of the model file
    """

    __tablename__ = "model_upload"
    id = Column(Integer(), Sequence("model_upload_id_seq"), primary_key=True)
    model_id = Column(Integer(), ForeignKey("model_info.id"))
    user_id = Column(Integer())
    register_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    file_name = Column(String())
    file_path = Column(String())
    # {0 - Model Policy File Upload  , 1 - Model File Upload}
    file_type = Column(Integer(), CheckConstraint("file_type IN (0, 1)"))
    file_description = Column(String())
    # Define the many-to-one relationship with ModelInfo
    model_info = relationship("ModelInfo", back_populates="model_uploads")
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "file_name",
            "model_id",
            name="unique_filename_per_user_per_model",
        ),
    )
