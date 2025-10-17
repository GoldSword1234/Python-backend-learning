import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    f"postgresql://{os.getenv('DATABASE_USER', 'username')}:"
    f"{os.getenv('DATABASE_PASSWORD', 'password')}@"
    f"{os.getenv('DATABASE_HOST', 'localhost')}:"
    f"{os.getenv('DATABASE_PORT', '5432')}/"
    f"{os.getenv('DATABASE_NAME', 'your_database')}"
)

try:
    # Create SQLAlchemy engine with connection pooling and error handling
    engine = create_engine(
        DATABASE_URL,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,  # Validate connections before use
        pool_recycle=3600,   # Recycle connections after 1 hour
        echo=os.getenv("DEBUG", "False").lower() == "true"  # Log SQL queries in debug mode
    )
    
    # Test connection
    with engine.connect() as conn:
        pass
    
    # Create session factory
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Create declarative base for models
    Base = declarative_base()
    
    logger.info("Database configuration initialized successfully")
    
except Exception as e:
    logger.warning(f"Database connection failed: {e}")
    logger.info("Creating engine without testing connection for development mode")
    
    # Create engine without testing connection (for development without DB)
    engine = create_engine(
        DATABASE_URL,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        pool_recycle=3600,
        echo=os.getenv("DEBUG", "False").lower() == "true"
    )
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base = declarative_base()

# Dependency to get database session
def get_db():
    """Dependency that provides a database session.
    
    Yields:
        Session: SQLAlchemy database session
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()