"""Read-only database connectors."""
from .base import (ConnectionInfo, Connector, ConnectorError, ReadOnlyViolation, assert_read_only, open_connector,
                   parse_url, redact_url, register_connector, sql_references)
from .mysql import MySQLConnector
from .postgres import PostgresConnector
from .sqlite import SQLiteConnector

register_connector("postgresql", PostgresConnector)
register_connector("mysql", MySQLConnector)
register_connector("sqlite", SQLiteConnector)

__all__ = [
    "ConnectionInfo", "Connector", "ConnectorError", "MySQLConnector", "PostgresConnector", "ReadOnlyViolation",
    "SQLiteConnector", "assert_read_only", "open_connector", "parse_url", "redact_url", "register_connector",
    "sql_references",
]
