from services.configuration.config import settings
from mysql.connector import pooling, Error
from fastapi import HTTPException
from services.configuration.logger import get_logger

logger = get_logger("Execution_Logger")

class MysqlDB:

    def __init__(self):
        self.pool = None
        self.initialize_pool()

    def initialize_pool(self):
        try:
            self.pool = pooling.MySQLConnectionPool(
                pool_name=settings.POOL_NAME,
                pool_size=settings.POOL_SIZE,
                pool_reset_session=settings.POOL_RESET_SESSION,
                host=settings.HOST_NAME,
                user=settings.USER_NAME,
                password=settings.PASSWORD,
                database=settings.DATABASE_NAME,
                connect_timeout=10,
            )
            logger.info("MySQL connection pool initialized successfully.")
        except Error as e:
            logger.error(f"MySQL connection pool initialization failed: {e}")
            raise HTTPException(status_code=500, detail="Unable to establish MySQL database connection.")

    def Execute_Query(self, sql_query: str, params=None) -> list[dict]:
        if not self.pool:
            logger.error("Attempted to execute a query without an initialized MySQL connection pool.")
            raise HTTPException(status_code=500, detail="MySQL connection is not initialized.")

        connection = None
        cursor=None
        try:
            connection = self.pool.get_connection()
            cursor = connection.cursor()
            cursor.execute(sql_query, params or ())
            columns = [col[0] for col in cursor.description]
            results = [dict(zip(columns, row)) for row in cursor.fetchall()]

            if not results:
                logger.warning(f"No data found for query: {sql_query}")
                raise HTTPException(status_code=404, detail="No data found for the given query.")

            logger.debug(f"Query executed successfully with {len(results)} rows returned.")
            return results

        except Error as e:
            logger.error(f"MySQL error occurred during query execution: {e}")
            raise HTTPException(status_code=400, detail="Error executing the MySQL query.")

        except Exception as e:
            logger.exception(f"Unexpected error while executing MySQL query: {sql_query}")
            raise HTTPException(status_code=500, detail="Internal server error during query execution.")

        finally:
            if connection and connection.is_connected():
                cursor.close()
                connection.close()
                logger.info("MySQL connection released back to pool.")

    def close_pool(self):
        self.pool = None
        logger.info("MySQL pool reference cleared")
