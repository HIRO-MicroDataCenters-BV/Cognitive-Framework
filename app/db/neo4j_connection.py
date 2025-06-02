"""
This module provides a connection to a Neo4j database and methods to execute queries.
"""

from typing import List, Optional, Dict, Any
from neo4j import GraphDatabase
from neo4j.exceptions import Neo4jError


class Neo4jConnection:
    """Handles connection to a Neo4j database."""

    def __init__(self, uri: str, user: str, password: str):
        """
        Initialize the Neo4jConnection with the given URI, user, and password.

        :param uri: The URI of the Neo4j database.
        :param user: The username for authentication.
        :param password: The password for authentication.
        """
        try:
            self._driver = GraphDatabase.driver(uri, auth=(user, password))
        except Neo4jError as neo4j_error:
            raise RuntimeError(f"Failed to create the driver: {neo4j_error}")

    def close(self) -> None:
        """Close the connection to the Neo4j database."""
        if self._driver:
            self._driver.close()

    def query(
        self, query: str, parameters: Optional[Dict[str, Any]] = None, **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Execute a query against the Neo4j database.

        :param query: The Cypher query to execute.
        :param parameters: Optional parameters for the query.
        :return: A list of dictionaries representing the query results.
        """
        parameters = parameters or {}
        try:
            with self._driver.session() as session:
                result = session.run(query, parameters, **kwargs)
                return [record.data() for record in result]
        except Neo4jError as neo4j_error:
            raise RuntimeError(f"Query failed: {neo4j_error}")
