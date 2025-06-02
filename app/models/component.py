"""
    DB model class for component.
"""

from sqlalchemy import Column, Integer, String, Sequence, JSON
from app.db.session import Base


class Component(Base):
    """
    DB model class for Table.

    The following attributes of the Table are stored in this table:
        * id - Unique identifier for the Table
        * name - Name of the Table
        * input_path - Input path (can be a string, vector, or dictionary)
        * output_path - Output path (can be a string, vector, or dictionary)
    """

    __tablename__ = "component"
    id = Column(Integer, Sequence("table_id_seq"), primary_key=True)
    name = Column(String, nullable=False)
    input_path = Column(JSON, nullable=False)
    output_path = Column(JSON, nullable=False)
    component_file = Column(String)
