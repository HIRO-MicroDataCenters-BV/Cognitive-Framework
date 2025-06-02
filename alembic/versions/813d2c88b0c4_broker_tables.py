"""broker_tables

Revision ID: 813d2c88b0c4
Revises: 969bb48172d7
Create Date: 2024-12-24 13:29:21.835393

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine import Inspector

# revision identifiers, used by Alembic.
revision: str = "813d2c88b0c4"
down_revision: Union[str, None] = "969bb48172d7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Get the current connection
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)

    # Check if the table already exists
    if "broker_details" not in inspector.get_table_names():
        op.create_table(
            "broker_details",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("broker_name", sa.String(), nullable=False),
            sa.Column("broker_ip", sa.String(), nullable=False),
            sa.Column("creation_date", sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("broker_name", name="unique_broker_per_dataset"),
        )

    if "dataset_info" not in inspector.get_table_names():
        op.create_table(
            "dataset_info",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("train_and_inference_type", sa.Integer(), nullable=True),
            sa.Column("data_source_type", sa.Integer(), nullable=True),
            sa.Column("dataset_name", sa.String(), nullable=True),
            sa.Column("description", sa.String(), nullable=True),
            sa.Column("user_id", sa.Integer(), nullable=True),
            sa.Column("register_date_time", sa.DateTime(), nullable=False),
            sa.Column("last_modified_time", sa.DateTime(), nullable=False),
            sa.Column("last_modified_user_id", sa.Integer(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )

    if "ix_dataset_info_id" not in [
        index["name"] for index in inspector.get_indexes("dataset_info")
    ]:
        op.create_index(
            op.f("ix_dataset_info_id"), "dataset_info", ["id"], unique=False
        )

    if "experiments" not in inspector.get_table_names():
        op.create_table(
            "experiments",
            sa.Column("uuid", sa.String(length=255), nullable=False),
            sa.Column("name", sa.String(length=255), nullable=False),
            sa.Column("description", sa.String(length=255), nullable=False),
            sa.Column("createdatinSec", sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint("uuid"),
        )

    if "model_info" not in inspector.get_table_names():
        op.create_table(
            "model_info",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("name", sa.String(), nullable=True),
            sa.Column("version", sa.String(), nullable=True),
            sa.Column("register_date", sa.DateTime(), nullable=False),
            sa.Column("register_user_id", sa.Integer(), nullable=True),
            sa.Column("type", sa.String(), nullable=True),
            sa.Column("description", sa.String(), nullable=True),
            sa.Column("last_modified_time", sa.DateTime(), nullable=False),
            sa.Column("last_modified_user_id", sa.Integer(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )

    if "dataset_file_details" not in inspector.get_table_names():
        op.create_table(
            "dataset_file_details",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("dataset_id", sa.Integer(), nullable=True),
            sa.Column("user_id", sa.Integer(), nullable=True),
            sa.Column("register_date", sa.DateTime(), nullable=False),
            sa.Column("file_path", sa.String(), nullable=True),
            sa.Column("file_name", sa.String(), nullable=True),
            sa.ForeignKeyConstraint(
                ["dataset_id"],
                ["dataset_info.id"],
            ),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint(
                "user_id", "file_name", name="unique_filename_per_user"
            ),
        )

    if "ix_dataset_file_details_id" not in [
        index["name"] for index in inspector.get_indexes("dataset_file_details")
    ]:
        op.create_index(
            op.f("ix_dataset_file_details_id"),
            "dataset_file_details",
            ["id"],
            unique=False,
        )

    if "dataset_table_details" not in inspector.get_table_names():
        op.create_table(
            "dataset_table_details",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("dataset_id", sa.Integer(), nullable=True),
            sa.Column("user_id", sa.Integer(), nullable=True),
            sa.Column("register_date", sa.DateTime(), nullable=False),
            sa.Column("db_url", sa.String(), nullable=True),
            sa.Column("table_name", sa.String(), nullable=True),
            sa.Column("fields_selected_list", sa.String(), nullable=True),
            sa.ForeignKeyConstraint(
                ["dataset_id"],
                ["dataset_info.id"],
            ),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint(
                "user_id", "table_name", name="unique_table_per_user_id"
            ),
        )

    if "ix_dataset_table_details_id" not in [
        index["name"] for index in inspector.get_indexes("dataset_table_details")
    ]:
        op.create_index(
            op.f("ix_dataset_table_details_id"),
            "dataset_table_details",
            ["id"],
            unique=False,
        )

    if "model_dataset" not in inspector.get_table_names():
        op.create_table(
            "model_dataset",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("model_id", sa.Integer(), nullable=False),
            sa.Column("dataset_id", sa.Integer(), nullable=False),
            sa.Column("linked_time", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(
                ["dataset_id"], ["dataset_info.id"], ondelete="CASCADE"
            ),
            sa.ForeignKeyConstraint(
                ["model_id"], ["model_info.id"], ondelete="CASCADE"
            ),
            sa.PrimaryKeyConstraint("id"),
        )

    if "model_upload" not in inspector.get_table_names():
        op.create_table(
            "model_upload",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("model_id", sa.Integer(), nullable=True),
            sa.Column("user_id", sa.Integer(), nullable=True),
            sa.Column("register_date", sa.DateTime(), nullable=False),
            sa.Column("file_name", sa.String(), nullable=True),
            sa.Column("file_path", sa.String(), nullable=True),
            sa.Column("file_type", sa.Integer(), nullable=True),
            sa.Column("file_description", sa.String(), nullable=True),
            sa.ForeignKeyConstraint(
                ["model_id"],
                ["model_info.id"],
            ),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint(
                "user_id",
                "file_name",
                "model_id",
                name="unique_filename_per_user_per_model",
            ),
        )

    if "pipelines" not in inspector.get_table_names():
        op.create_table(
            "pipelines",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("uuid", sa.String(length=255), nullable=True),
            sa.Column("model_id", sa.Integer(), nullable=True),
            sa.Column("createdAt_in_sec", sa.DateTime(), nullable=False),
            sa.Column("name", sa.String(length=255), nullable=False),
            sa.Column("description", sa.String(length=255), nullable=False),
            sa.Column("parameters", sa.String(), nullable=True),
            sa.Column("status", sa.String(length=255), nullable=True),
            sa.Column("experiment_uuid", sa.String(length=255), nullable=False),
            sa.Column("pipeline_spec", sa.String(), nullable=True),
            sa.Column("pipeline_spec_uri", sa.String(), nullable=True),
            sa.ForeignKeyConstraint(
                ["experiment_uuid"],
                ["experiments.uuid"],
            ),
            sa.ForeignKeyConstraint(
                ["model_id"],
                ["model_info.id"],
            ),
            sa.PrimaryKeyConstraint("id"),
        )

    if "run_details" not in inspector.get_table_names():
        op.create_table(
            "run_details",
            sa.Column("uuid", sa.String(length=255), nullable=False),
            sa.Column("display_name", sa.String(length=255), nullable=False),
            sa.Column("name", sa.String(length=255), nullable=False),
            sa.Column("description", sa.String(length=255), nullable=True),
            sa.Column("experiment_uuid", sa.String(length=255), nullable=False),
            sa.Column("pipeline_uuid", sa.String(length=255), nullable=False),
            sa.Column("createdAt_in_sec", sa.DateTime(), nullable=False),
            sa.Column("scheduledAt_in_sec", sa.DateTime(), nullable=True),
            sa.Column("finishedAt_in_sec", sa.DateTime(), nullable=True),
            sa.Column("state", sa.String(length=255), nullable=True),
            sa.ForeignKeyConstraint(
                ["experiment_uuid"],
                ["experiments.uuid"],
            ),
            sa.PrimaryKeyConstraint("uuid"),
        )

    if "topic_details" not in inspector.get_table_names():
        op.create_table(
            "topic_details",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("topic_name", sa.String(), nullable=True),
            sa.Column("topic_schema", sa.JSON(), nullable=True),
            sa.Column("broker_id", sa.Integer(), nullable=True),
            sa.Column("creation_date", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(
                ["broker_id"],
                ["broker_details.id"],
            ),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint(
                "topic_name", "broker_id", name="unique_topic_per_broker"
            ),
        )

    if "validation_artifact" not in inspector.get_table_names():
        op.create_table(
            "validation_artifact",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("model_id", sa.Integer(), nullable=True),
            sa.Column("dataset_id", sa.Integer(), nullable=True),
            sa.Column("validation_artifacts", sa.JSON(), nullable=True),
            sa.ForeignKeyConstraint(
                ["dataset_id"],
                ["dataset_info.id"],
            ),
            sa.ForeignKeyConstraint(
                ["model_id"],
                ["model_info.id"],
            ),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint(
                "model_id", "dataset_id", name="unique_model_id_dataset_id"
            ),
        )

    if "validation_metric" not in inspector.get_table_names():
        op.create_table(
            "validation_metric",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("model_id", sa.Integer(), nullable=True),
            sa.Column("dataset_id", sa.Integer(), nullable=True),
            sa.Column("registered_date_time", sa.DateTime(), nullable=False),
            sa.Column("accuracy_score", sa.Float(), nullable=True),
            sa.Column("example_count", sa.Integer(), nullable=True),
            sa.Column("f1_score", sa.Float(), nullable=True),
            sa.Column("log_loss", sa.Float(), nullable=True),
            sa.Column("precision_score", sa.Float(), nullable=True),
            sa.Column("recall_score", sa.Float(), nullable=True),
            sa.Column("roc_auc", sa.Integer(), nullable=True),
            sa.Column("score", sa.Float(), nullable=True),
            sa.Column("cpu_consumption", sa.Float(), nullable=True),
            sa.Column("memory_utilization", sa.Float(), nullable=True),
            sa.ForeignKeyConstraint(
                ["dataset_id"],
                ["dataset_info.id"],
            ),
            sa.ForeignKeyConstraint(
                ["model_id"],
                ["model_info.id"],
            ),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint(
                "model_id", "dataset_id", name="unique_model_id_dataset_id_per_metric"
            ),
        )

    if "dataset_topic_details" not in inspector.get_table_names():
        op.create_table(
            "dataset_topic_details",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("topic_id", sa.Integer(), nullable=True),
            sa.Column("dataset_id", sa.Integer(), nullable=True),
            sa.Column("creation_date", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(
                ["dataset_id"],
                ["dataset_info.id"],
            ),
            sa.ForeignKeyConstraint(
                ["topic_id"],
                ["topic_details.id"],
            ),
            sa.PrimaryKeyConstraint("id"),
        )

    if "ix_dataset_topic_details_id" not in [
        index["name"] for index in inspector.get_indexes("dataset_topic_details")
    ]:
        op.create_index(
            op.f("ix_dataset_topic_details_id"),
            "dataset_topic_details",
            ["id"],
            unique=False,
        )

    if "tasks" not in inspector.get_table_names():
        op.create_table(
            "tasks",
            sa.Column("uuid", sa.String(length=255), nullable=False),
            sa.Column("runuuid", sa.String(length=255), nullable=False),
            sa.Column("createdtimestamp", sa.DateTime(), nullable=False),
            sa.Column("startedtimestamp", sa.DateTime(), nullable=False),
            sa.Column("finishedtimestamp", sa.DateTime(), nullable=False),
            sa.Column("state", sa.String(length=255), nullable=True),
            sa.Column("name", sa.String(length=255), nullable=True),
            sa.Column("parenttaskuuid", sa.String(length=255), nullable=True),
            sa.ForeignKeyConstraint(
                ["runuuid"],
                ["run_details.uuid"],
            ),
            sa.PrimaryKeyConstraint("uuid"),
        )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("tasks")
    op.drop_index(
        op.f("ix_dataset_topic_details_id"), table_name="dataset_topic_details"
    )
    op.drop_table("dataset_topic_details")
    op.drop_table("validation_metric")
    op.drop_table("validation_artifact")
    op.drop_table("topic_details")
    op.drop_table("run_details")
    op.drop_table("pipelines")
    op.drop_table("model_upload")
    op.drop_table("model_dataset")
    op.drop_index(
        op.f("ix_dataset_table_details_id"), table_name="dataset_table_details"
    )
    op.drop_table("dataset_table_details")
    op.drop_index(op.f("ix_dataset_file_details_id"), table_name="dataset_file_details")
    op.drop_table("dataset_file_details")
    op.drop_table("model_info")
    op.drop_table("experiments")
    op.drop_index(op.f("ix_dataset_info_id"), table_name="dataset_info")
    op.drop_table("dataset_info")
    op.drop_table("broker_details")
    # ### end Alembic commands ###
