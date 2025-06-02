"""
file to update alembic.ini
"""

import os
import configparser
from config import constants as const


def update_alembic_ini() -> None:
    """
    Update the alembic.ini file with the database URL
    Returns:
        None
    """
    db_user = os.getenv(const.DB_USER)
    db_password = os.getenv(const.DB_PASSWORD)
    db_host = os.getenv(const.DB_HOST)
    db_port = os.getenv(const.DB_PORT)
    db_name = os.getenv(const.DB_NAME)

    # Construct the database URL without the invalid option
    database_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

    # Read the alembic.ini file
    config = configparser.ConfigParser()
    config.read("alembic.ini")

    # Update the sqlalchemy.url
    config.set("alembic", "sqlalchemy.url", database_url)

    # Write the changes back to alembic.ini
    with open("alembic.ini", "w", encoding="utf-8") as configfile:
        config.write(configfile)
