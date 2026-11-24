
import sqlite3
from pathlib import Path

# Project directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Database directory and file
DATABASE_DIR = BASE_DIR / "database"
DATABASE_PATH = DATABASE_DIR / "civictrack.db"


def get_connection():
    """
    Create and return a SQLite database connection.
    """

    DATABASE_DIR.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(
        str(DATABASE_PATH),
        check_same_thread=False
    )

    connection.row_factory = sqlite3.Row

    # Enable foreign key relationships
    connection.execute("PRAGMA foreign_keys = ON")

    return connection


def initialize_database():
    """
    Ensure that the database file exists.
    Table creation will be handled by create_tables.py.
    """

    connection = get_connection()
    connection.close()

    return DATABASE_PATH


def execute_query(query, parameters=(), fetchone=False, fetchall=False):
    """
    Execute a database query safely using parameterized SQL.
    """

    connection = get_connection()

    try:
        cursor = connection.cursor()
        cursor.execute(query, parameters)

        if fetchone:
            result = cursor.fetchone()
            return dict(result) if result else None

        if fetchall:
            return [dict(row) for row in cursor.fetchall()]

        connection.commit()
        return cursor.lastrowid

    except sqlite3.Error:
        connection.rollback()
        raise

    finally:
        connection.close()
