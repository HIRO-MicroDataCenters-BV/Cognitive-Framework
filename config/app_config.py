"""
Configuration settings for different environments.

This module defines configuration settings for development and production environments.

Classes:
    DevelopmentConfig: Configuration settings for the development environment.
    ProductionConfig: Configuration settings for the production environment.
"""


class DevelopmentConfig:
    """
    Configuration settings for the development environment.

    Attributes:
        DEBUG (bool): Enable or disable debug mode.
        DATABASE_URL (str): The database URL for the development environment.
    """

    DEBUG = True
    DATABASE_URL = "sqlite:///./test.db"


class TestingConfig:
    """
    Configuration settings for the testing environment.

    Attributes:
        DEBUG (bool): Enable or disable debug mode.
        DATABASE_URL (str): The database URL for the development environment.
    """

    DEBUG = True
    DATABASE_URL = "sqlite:///./test.db"


class ProductionConfig:
    """
    Configuration settings for the production environment.

    Attributes:
        DEBUG (bool): Enable or disable debug mode.
        DATABASE_URL (str): The database URL for the production environment.
    """

    DEBUG = False
    DATABASE_URL = "sqlite:///./prod.db"
    DB_URI = "bolt://localhost:7687"
    DB_USER = "neo4j"
    DB_PASSWORD = "password"
