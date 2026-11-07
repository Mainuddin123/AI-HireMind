
from sqlalchemy import text

from backend.database.connection import engine


def test_database_connection():
    try:
        with engine.connect() as connection:

            result = connection.execute(
                text("SELECT DATABASE(), VERSION()")
            )

            database_name, mysql_version = result.fetchone()

            print("MySQL connection successful!")
            print(f"Database: {database_name}")
            print(f"MySQL Version: {mysql_version}")

    except Exception as error:
        print("Database connection failed!")
        print(f"Error: {type(error).__name__}: {error}")


if __name__ == "__main__":
    test_database_connection()
