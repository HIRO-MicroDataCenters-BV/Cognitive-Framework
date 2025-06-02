"""
    DB model class for DatasetUpload
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.db.session import Base


class DatasetFileDetails(Base):
    """
    Class that represents dataset_file_details information
    The following attributes of a dataset_upload are stored in this table:
    * id - id of the dataset upload
    * dataset_id - dataset id
    * user_id - user who registered the  dataset
    * register_date - date of registering the  dataset
    * file_path - file path of the  dataset
    * file_name - file name of the  dataset
    """

    __tablename__ = "dataset_file_details"
    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, ForeignKey("dataset_info.id"))
    user_id = Column(Integer)
    register_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    file_path = Column(String)
    file_name = Column(String)  # UNIQUE Combination with user_id
    dataset_info = relationship("DatasetInfo", back_populates="dataset_uploads")
    __table_args__ = (
        UniqueConstraint("user_id", "file_name", name="unique_filename_per_user"),
    )
