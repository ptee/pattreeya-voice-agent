"""
Database connection manager with pooling for PostgreSQL
Provides abstraction for database queries and connection management
"""

import logging
from typing import Any, Dict, List, Optional, Tuple
from contextlib import contextmanager

import psycopg2
from psycopg2.pool import SimpleConnectionPool
from psycopg2.extras import RealDictCursor

from config import get_config

logger = logging.getLogger("db_manager")


class DatabaseManager:
    """Manages database connections and queries with connection pooling"""

    _instance: Optional["DatabaseManager"] = None
    _pool: Optional[SimpleConnectionPool] = None

    def __init__(self, config=None):
        """
        Initialize database manager with connection pool

        Args:
            config: Optional ConfigManager instance. If None, uses get_config()

        Raises:
            Exception: If connection pool initialization fails
        """
        self.config = config or get_config()

        try:
            # Create connection pool: 5 min connections, 10 max connections
            self._pool = SimpleConnectionPool(
                minconn=5,
                maxconn=10,
                dsn=self.config.get_postgresql_url(),
                connect_timeout=5,
            )
            logger.info("Database connection pool initialized (5-10 connections)")
        except Exception as e:
            logger.error(f"Failed to initialize database connection pool: {e}")
            raise

    @contextmanager
    def get_connection(self):
        """
        Context manager for getting a database connection from the pool

        Yields:
            psycopg2 connection object

        Example:
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM table")
        """
        conn = None
        try:
            conn = self._pool.getconn()
            yield conn
        finally:
            if conn:
                self._pool.putconn(conn)

    @contextmanager
    def get_cursor(self, cursor_factory=None):
        """
        Context manager for getting a database cursor with automatic commit/rollback

        Args:
            cursor_factory: Optional cursor factory class (e.g., RealDictCursor)

        Yields:
            psycopg2 cursor object

        Example:
            with db_manager.get_cursor() as cursor:
                cursor.execute("SELECT * FROM table")
                results = cursor.fetchall()
        """
        with self.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=cursor_factory)
            try:
                yield cursor
                conn.commit()
            except Exception as e:
                conn.rollback()
                logger.error(f"Database transaction rolled back: {e}")
                raise
            finally:
                cursor.close()

    def execute_query(
        self,
        query: str,
        params: Tuple = (),
        fetch_all: bool = True,
        as_dict: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Execute a SELECT query and return results

        Args:
            query: SQL query string
            params: Query parameters as tuple
            fetch_all: If True, fetch all results; if False, fetch one
            as_dict: If True, return results as dicts; if False, return tuples

        Returns:
            List of results (as dicts or tuples)

        Raises:
            Exception: If query execution fails
        """
        try:
            cursor_factory = RealDictCursor if as_dict else None

            with self.get_cursor(cursor_factory=cursor_factory) as cursor:
                cursor.execute(query, params)

                if fetch_all:
                    rows = cursor.fetchall()
                else:
                    row = cursor.fetchone()
                    rows = [row] if row else []

                return list(rows) if rows else []

        except Exception as e:
            logger.error(f"Query execution failed: {e}", extra={"query": query[:100]})
            raise

    def execute_insert_update(
        self, query: str, params: Tuple = ()
    ) -> int:
        """
        Execute an INSERT, UPDATE, or DELETE query

        Args:
            query: SQL query string
            params: Query parameters as tuple

        Returns:
            Number of rows affected

        Raises:
            Exception: If query execution fails
        """
        try:
            with self.get_cursor() as cursor:
                cursor.execute(query, params)
                return cursor.rowcount

        except Exception as e:
            logger.error(f"Query execution failed: {e}", extra={"query": query[:100]})
            raise

    def execute_batch(
        self, query: str, params_list: List[Tuple]
    ) -> int:
        """
        Execute a query multiple times with different parameters (batch insert/update)

        Args:
            query: SQL query string
            params_list: List of parameter tuples

        Returns:
            Total number of rows affected

        Raises:
            Exception: If batch execution fails
        """
        try:
            with self.get_cursor() as cursor:
                total_rows = 0
                for params in params_list:
                    cursor.execute(query, params)
                    total_rows += cursor.rowcount
                return total_rows

        except Exception as e:
            logger.error(f"Batch execution failed: {e}")
            raise

    def close(self) -> None:
        """Close all connections in the pool"""
        try:
            if self._pool:
                self._pool.closeall()
                logger.info("Database connection pool closed")
        except Exception as e:
            logger.error(f"Error closing database pool: {e}")

    @classmethod
    def get_instance(cls, config=None) -> "DatabaseManager":
        """
        Get or create the singleton database manager instance

        Args:
            config: Optional ConfigManager instance

        Returns:
            DatabaseManager instance
        """
        if cls._instance is None:
            cls._instance = cls(config)
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset the singleton instance (useful for testing)"""
        if cls._instance:
            cls._instance.close()
        cls._instance = None


def get_db_manager(config=None) -> DatabaseManager:
    """
    Get the global database manager instance

    Args:
        config: Optional ConfigManager instance

    Returns:
        DatabaseManager instance
    """
    return DatabaseManager.get_instance(config)


# Helper functions for common operations

def convert_dates(record: Dict[str, Any], date_fields: List[str]) -> None:
    """
    Convert date fields in a record to strings (in-place modification)

    Args:
        record: Dictionary containing the record
        date_fields: List of field names to convert
    """
    for field in date_fields:
        if field in record and record[field]:
            record[field] = str(record[field])


def convert_array_fields(record: Dict[str, Any], array_fields: List[str]) -> None:
    """
    Convert PostgreSQL array strings to Python lists (in-place modification)

    PostgreSQL arrays like '{a,b,c}' are converted to ['a', 'b', 'c']

    Args:
        record: Dictionary containing the record
        array_fields: List of field names to convert
    """
    for field in array_fields:
        if field in record and isinstance(record[field], str):
            # Remove braces and split on comma
            value = record[field].strip("{}")
            record[field] = [item.strip() for item in value.split(",")] if value else []


if __name__ == "__main__":
    # Simple test
    import logging

    logging.basicConfig(level=logging.INFO)

    try:
        db = get_db_manager()
        print("✓ Database manager initialized successfully")
        print(f"  Connection pool: 5-10 connections")

        # Test a simple query
        result = db.execute_query("SELECT 1 as test_value", as_dict=True)
        if result:
            print(f"✓ Test query successful: {result[0]}")
        else:
            print("✗ Test query returned no results")

    except Exception as e:
        print(f"✗ Database manager error: {e}")