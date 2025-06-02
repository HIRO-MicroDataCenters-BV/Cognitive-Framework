"""
    DB model class for Pipeline.
"""

from sqlalchemy import Column, Integer, String, Sequence, JSON
from app.db.session import Base


class PipelineComponent(Base):
    """
    DB model class for Pipeline.

    The following attributes of the Pipeline are stored in this table:
        * id - Unique identifier for the Pipeline
        * name - Name of the Pipeline
        * pipeline_components - JSON links to pipeline components
        * input_path - Input path
        * output_path - Output path
    """

    __tablename__ = "pipeline_component"
    id = Column(Integer, Sequence("pipeline_id_seq"), primary_key=True)
    name = Column(String, nullable=False)
    pipeline_components = Column(JSON, nullable=False)
    input_path = Column(JSON, nullable=False)
    output_path = Column(JSON, nullable=False)
