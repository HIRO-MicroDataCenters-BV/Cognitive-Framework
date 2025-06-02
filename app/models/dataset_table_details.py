"""
    DB model class for Dataset Table register
"""

from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    DateTime,
    String,
    UniqueConstraint,
    ForeignKey,
)
from sqlalchemy.orm import relationship

from app.db.session import Base


class DatasetTableDetails(Base):
    """
    Class that represents dataset_table_details information
    The following attributes of a dataset_table_details are stored in this table:
    * id - id of the dataset
    * dataset_id - dataset id
    * user_id - user id who registered the  dataset
    * register_date - date of registering the dataset
    * db_url - url of the db
    * table_name - name of the table to be registered as dataset
    * fields_selected_list - list of fields selected
    """

    __tablename__ = "dataset_table_details"
    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, ForeignKey("dataset_info.id"))
    user_id = Column(Integer)
    register_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    db_url = Column(String)
    table_name = Column(String)
    fields_selected_list = Column(String)
    dataset_info = relationship(
        "DatasetInfo", back_populates="dataset_table_registraters"
    )
    __table_args__ = (
        UniqueConstraint("user_id", "table_name", name="unique_table_per_user_id"),
    )
