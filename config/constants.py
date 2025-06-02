"""
This file contains constants used throughout the application.
"""

import os

DATA_SOURCE_TYPE_FILE = 0
DATA_SOURCE_TYPE_TABLE = 1
BROKER_DATA_SOURCE_TYPE = 2
USER_ID = 0  # Fix: be replaced with user service module
FILE_UPLOAD_PATH = "var/data/"
CONFIG_DIR = "config"
CONFIG_FILE = "config.cfg"
LOGGING_CONF = "logging.ini"
LOG_FORMAT = (
    "[%(asctime)s] | %(remote_addr)s | requested %(url)s "
    "| %(levelname)s  |%(module)s | %(funcName)s | %(message)s"
)
PROJECT_ROOT_DIR = os.path.abspath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
)
# configure logs to your specific logs directory
LOGS_DIR = "var/logs"
WELCOME_MSG = "Cognitive Framework Service!"
HEALTH_MSG = "Cognitive Framework Health Service Up!"
# configure data to your specific data directory
DOWNLOAD_DIR = "var/data/"
APP_NAME = "Cognitive Framework"
MODEL_REGISTER_KEYS_TO_UPDATE = ["name", "version", "type", "user_id"]
CONFIG_FILE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), CONFIG_FILE)
DEVELOPMENT_CONFIG = "config.app_config.DevelopmentConfig"
PRODUCTION_CONFIG = "config.app_config.ProductionConfig"
DATASET_VALUE_ERROR = "is not a valid DatasetTypeEnum"
DB_UNIQUE_ERROR = "psycopg2.errors.UniqueViolation"
DB_FOREIGN_KEY_ERROR = "psycopg2.errors.ForeignKeyViolation"
DATASET_TYPE_ERROR_MESSAGE = "not a valid DatasetTypeEnum"

MODEL_TYPE_ERROR_MESSAGE = "Invalid file type : Must be a 0 or 1. 0 - Model Policy File Upload , 1 - Model File Upload"

# Database variables
DB_USER = "DB_USER"
DB_PASSWORD = "DB_PASSWORD"
DB_HOST = "DB_HOST"
DB_PORT = "DB_PORT"
DB_NAME = "DB_NAME"

# Minio Storage details
BUCKET_NAME = "mlflow"
MINIO_CLIENT_NAME = "s3"

# Testing Configuration
SQLALCHEMY_TEST_DATABASE_URI = "sqlite://"
TESTING_CONFIG = "config.app_config.TestingConfig"
TEST_FILE_NAME = "Iris.txt"
TEST_FILE_NAME2 = "Iris2.txt"

# Support types
TYPES = {"zip", "csv", "dat", "bin", "txt"}

# Invalid Duration Msg
INVALID_DATE_SELECT = "Number of days cannot be negative."
INVALID_DATE_RANGE_SELECT = "Number of days cannot be greater than 365."
NON_LEAP_YEAR_DAYS = 365
LEAP_YEAR_DAYS = 366
PIPELINE_MODEL_ID_ERROR_MSG = "Pipeline with Model ID Not Found"
PIPELINE_ID_ERROR_MSG = "Pipeline ID Not Found"
PIPELINE_DEL_EXCEPTION_MSG = (
    "Exception occurred while deleting Pipeline for the given details pipeline id"
)
RUN_EXCEPTION_MSG = (
    "Exception occurred while fetching Run Details for the given pipeline id"
)
RUN_DEL_EXCEPTION_MSG = (
    "Exception occurred while fetching Run Details for the given pipeline id"
)
RUN_NOT_FOUND = "No Runs Found"

MODEL_NOT_FOUND = "Model Not Found"
MINIO_CLIENT_ERROR = "Minio Client error"

# Validation metrics inputs
MODEL_NAME = "model_name"
ACCURACY_SCORE = "accuracy_score"
EXAMPLE_COUNT = "example_count"
F1_SCORE = "f1_score"
LOG_LOSS = "log_loss"
PRECISION_SCORE = "precision_score"
RECALL_SCORE = "recall_score"
ROC_AUC = "roc_auc"
SCORE = "score"
CPU_CONSUMPTION = "cpu_consumption"
MEMORY_UTILIZATION = "memory_utilization"

# Broker Related
TOPIC_NAME = "topic_name"
BROKER_IP = "broker_ip"
BROKER_PORT = "broker_port"
DEFAULT_STREAM_DATA_COUNT = 200
STREAM_TIMEOUT = 10000
EARLIEST = "earliest"
LATEST = "latest"
