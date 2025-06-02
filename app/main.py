"""
This module contains the main FastAPI application instance and the function to create it.
"""

import os

from fastapi import FastAPI, APIRouter, Request
from sqlalchemy import inspect
from sqlalchemy_utils import database_exists, create_database
from starlette.middleware.cors import CORSMiddleware
from alembic import command
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory

from app.api.model_recommender import router as model_recommender_router
from app.api.models import router as model_register_router
from app.api.dataset import router as dataset_router
from app.api.users_api import router as users_router
from app.api.validation import router as validation_router
from app.api.pipeline_components import router as pipeline_component_router
from app.api.component import router as component_router
from app.api.kfp_pipelines import router as pipeline_router
from app.db.session import engine, Base
from app.middleware.logger import LoggerMiddleware, Mode, logger
from app.middleware.pagination import PaginationMiddleware
from app.db import update_alembic_ini
from app.utils.response_utils import standard_response

# from app.db.neo4j_connection import Neo4jConnection
from config import constants as const

# from config.app_config import ProductionConfig


router = APIRouter()
log = logger()

BASE_PATH = os.getenv("BASE_PATH", "/cogapi")


def get_db_version(engine) -> str:
    """
    Get the current version of the database by querying the alembic_version table.
    Args:
        engine: The SQLAlchemy engine.

    Returns:
        str: The current version of the database or an empty string if not found.
    """
    with engine.connect() as connection:
        context = MigrationContext.configure(connection)
        return context.get_current_revision() or ""


def get_latest_version(alembic_cfg: Config) -> str:
    """
    Get the latest version of the database using Alembic's ScriptDirectory.
    Args:
        alembic_cfg: Config object for Alembic.

    Returns:
        str: The latest version (head revision) of the database.
    """
    script = ScriptDirectory.from_config(alembic_cfg)
    return script.get_current_head() or ""


def check_and_upgrade_db() -> None:
    """
    Check the database version and upgrade if necessary, using Alembic's migration context and SQLAlchemy.
    Returns:
        None
    """
    update_alembic_ini.update_alembic_ini()
    alembic_cfg = Config("alembic.ini")
    script = ScriptDirectory.from_config(alembic_cfg)
    inspector = inspect(engine)
    if "alembic_version" not in inspector.get_table_names():
        with engine.connect() as connection:
            context = MigrationContext.configure(connection)
            context.stamp(script, "head")
    else:
        current_version = get_db_version(engine)
        latest_version = get_latest_version(alembic_cfg)

        if not current_version:
            with engine.connect() as connection:
                context = MigrationContext.configure(connection)
                context.stamp(script, "head")
        elif current_version != latest_version:
            with engine.connect() as connection:
                command.upgrade(alembic_cfg, "head")


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.

    Returns:
        FastAPI: The configured FastAPI application instance.
    """
    is_testing = os.getenv("TESTING", "False") == "True"

    if not database_exists(engine.url):
        initialise_db()
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()

    if len(existing_tables) < 2:
        initialise_db()

    if not is_testing:
        check_and_upgrade_db()

    application = FastAPI(
        title="Cognitive Framework API",
        version="2.0",
        docs_url=f"{BASE_PATH}/docs",
        redoc_url=f"{BASE_PATH}/redoc",
        openapi_url=f"{BASE_PATH}/openapi.json",
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    # Adding the pagination middleware to the FastAPI app
    application.add_middleware(PaginationMiddleware)
    application.add_middleware(LoggerMiddleware, mode=Mode.DEV)
    application.include_router(
        model_register_router, prefix=BASE_PATH, tags=["Models APIs"]
    )
    application.include_router(dataset_router, prefix=BASE_PATH, tags=["Datasets APIs"])
    application.include_router(
        validation_router, prefix=BASE_PATH, tags=["Validation APIs"]
    )
    application.include_router(
        model_recommender_router, prefix=BASE_PATH, tags=["Model Recommender API"]
    )
    application.include_router(
        pipeline_router, prefix=BASE_PATH, tags=["Pipeline APIs"]
    )
    application.include_router(
        component_router, prefix=BASE_PATH, tags=["Components APIs"]
    )
    application.include_router(
        pipeline_component_router, prefix=BASE_PATH, tags=["Pipeline components APIs"]
    )
    application.include_router(users_router, prefix=BASE_PATH, tags=["Users APIs"])
    application.include_router(router, prefix=BASE_PATH)

    return application


def initialise_db() -> None:
    """
    Initialize the database by creating all tables.
    """
    if not database_exists(engine.url):
        create_database(engine.url)
        print(f"Database created at {engine.url}")
    else:
        print(f"Database already exists at {engine.url}")

    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    cog_tables = Base.metadata.tables.keys()

    # Create tables in the correct order based on dependencies
    table_creation_order = [
        "model_info",
        "experiments",
        "run_details",
        "broker_details",
        "topic_details",
    ]

    for table in table_creation_order:
        if table not in existing_tables:
            Base.metadata.tables[table].create(bind=engine, checkfirst=True)

    for table in cog_tables:
        if table not in table_creation_order and table not in existing_tables:
            Base.metadata.tables[table].create(bind=engine, checkfirst=True)


@router.get("/")
def home():
    """
    return Home page
    """
    log.info("Home page loaded")

    return standard_response(status_code=200, message=const.WELCOME_MSG, data={})


@router.get("/health")
def health_check():
    """
    health check of server
    """
    return standard_response(status_code=200, message=const.HEALTH_MSG, data={})


@router.get("/headers")
async def get_headers(request: Request):
    """
    Get the headers from the request.
    """
    headers = dict(request.headers)

    return standard_response(status_code=200, message=const.HEALTH_MSG, data=headers)


# Not ready to use Neo4j yet
# neo4j_conn = Neo4jConnection(
#    uri=ProductionConfig.DB_URI,
#    user=ProductionConfig.DB_USER,
#    password=ProductionConfig.DB_PASSWORD,
# )
app = create_app()


# @app.on_event("shutdown")
# def shutdown_event():
#    """
#    Close the Neo4j connection when the FastAPI application
#    """
#    neo4j_conn.close()
#    log.info("Neo4j connection closed")
