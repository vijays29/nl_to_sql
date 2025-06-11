import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from services.configuration.logger import get_logger

# Initialize a logger for application configuration
logger = get_logger("app_configuration")

# Load environment variables from a .env file (overrides system variables if duplicates exist)
load_dotenv(override=True)

class Settings(BaseSettings):
    """
    Settings class to define and validate environment variables using Pydantic.
    This ensures structured, type-safe configuration management.
    """
    API_KEY: str                                  # API key for external services (e.g., Gemini)
    POOL_NAME: str = "mysql_pool"                 # Name assigned to MySQL connection pool
    HOST_NAME: str                                # Hostname or IP of the MySQL server
    USER_NAME: str                                # Username for MySQL authentication
    PASSWORD: str                                 # Password for MySQL authentication
    DATABASE_NAME: str                            # Name of the MySQL database
    POOL_RESET_SESSION: bool = True               # Whether to reset the session when a connection is reused
    CONNECT_TIMEOUT: int = 10                     # Timeout (in seconds) for establishing DB connections
    POOL_SIZE: int = 6                            # Maximum number of connections in the pool
    PINECONE_API_KEY: str                         # API key for Pinecone (vector database)
    INDEX_NAME: str                               # Pinecone index name used in retrieval-augmented generation

    class Config:
        """
        Configuration options for the Pydantic settings class.
        Reads variables from the specified .env file and allows extra fields without error.
        """
        env_file = ".env"
        extra = "allow"

# Instantiate the settings class to load all environment variables
settings = Settings()
logger.info("Configuration settings successfully loaded.")

# List of required environment variable names to validate application setup
required_vars = [
    'API_KEY', 'POOL_NAME', 'POOL_SIZE', 'HOST_NAME',
    'USER_NAME', 'PASSWORD', 'DATABASE_NAME',
    'POOL_RESET_SESSION', 'CONNECT_TIMEOUT',
    'PINECONE_API_KEY', 'INDEX_NAME'
]

# Check for any missing required variables and log an error if found
missing_vars = [var for var in required_vars if not getattr(settings, var, None)]
if missing_vars:
    logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
else:
    logger.info("All required environment variables are present.")
