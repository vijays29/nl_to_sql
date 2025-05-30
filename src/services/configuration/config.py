import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from services.configuration.logger import get_logger

logger = get_logger("config")

load_dotenv(override=True)

class Settings(BaseSettings):

    API_KEY:str
    POOL_NAME:str = "mysql_pool"
    HOST_NAME:str
    USER_NAME:str
    PASSWORD:str
    DATABASE_NAME:str  
    POOL_RESET_SESSION:bool = True
    CONNECT_TIMEOUT:int = 10
    POOL_SIZE:int=6
    PINECONE_API_KEY: str
    INDEX_NAME:str

    @classmethod
    def validate(cls):
        missing_vars = [var for var in ['API_KEY','POOL_NAME','POOL_SIZE','HOST_NAME', 'USER_NAME', 'PASSWORD', 'DATABASE_NAME','POOL_RESET_SESSION','CONNECT_TIMEOUT','PINECONE_API_KEY','INDEX_NAME'] if not getattr(cls, var)]
        if missing_vars:
            logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        else:
            logger.info("All required environment variables are present.")

    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()
logger.info("Settings object initialized successfully.")