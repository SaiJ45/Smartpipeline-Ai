from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
import logging

from config.settings import get_settings

# Setup logging
logger = logging.getLogger(__name__)

# Get settings
settings = get_settings()

# Create SQLAlchemy engine with connection pooling
engine = create_engine(
    settings.DATABASE_URL,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    echo=False  # Set to True for SQL debugging
)

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency injection function for FastAPI.
    
    Yields a database session and ensures it's closed after use.
    
    Usage in FastAPI:
        @app.get("/items/")
        def read_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    
    Yields:
        Session: SQLAlchemy database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_connection() -> None:
    """
    Test the database connection.
    
    Executes a simple 'SELECT 1' query and prints success or error message.
    """
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            result.fetchone()
        print("✓ Database connection successful")
        logger.info("Database connection successful")
    except Exception as e:
        error_message = f"✗ Database connection failed: {str(e)}"
        print(error_message)
        logger.error(error_message)
        raise
