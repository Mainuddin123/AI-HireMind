
from sqlalchemy import create_engine, URL
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from backend.config import settings


# Select database provider
if settings.database_provider.lower() == "tidb":

    # Validate TiDB configuration
    if not all([
        settings.tidb_host,
        settings.tidb_user,
        settings.tidb_password,
        settings.ca_path
    ]):
        raise ValueError("Missing required TiDB connection settings.")

    # Build TiDB connection URL
    DATABASE_URL = URL.create(
        drivername="mysql+pymysql",
        username=settings.tidb_user,
        password=settings.tidb_password,
        host=settings.tidb_host,
        port=settings.tidb_port,
        database=settings.tidb_db_name
    )

    # Create secure TiDB engine with TLS
    engine = create_engine(
        DATABASE_URL,
        connect_args={
            "ssl_ca": settings.ca_path,
            "ssl_verify_cert": True,
            "ssl_verify_identity": True
        },
        pool_pre_ping=True,
        pool_recycle=300,
        echo=settings.debug
    )

else:
    # Existing local MySQL connection
    DATABASE_URL = URL.create(
        drivername="mysql+pymysql",
        username=settings.db_user,
        password=settings.db_password,
        host=settings.db_host,
        port=settings.db_port,
        database=settings.db_name
    )

    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        echo=settings.debug
    )


# Database session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


# Base class for database models
class Base(DeclarativeBase):
    pass


# FastAPI database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
