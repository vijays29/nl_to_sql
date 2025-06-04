from services.configuration.config import settings
from mysql.connector import pooling, Error
from services.configuration.logger import get_logger

logger = get_logger("MysqlExecutionLogger")

class MysqlDB:
    def __init__(self):
        self.pool = None
        self.initialize_pool()

    def initialize_pool(self):
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
        logger.info("Initialized MySQL connection pool.")

    def Execute_Query(self, sql_query: str, params=None) -> list[dict]:
        if not self.pool:
            logger.error("MySQL connection pool is not initialized.")
            raise
        connection = None
        cursor=None
        try:
            connection = self.pool.get_connection()
            cursor = connection.cursor()
            cursor.execute(sql_query, params or ())
            columns = [col[0] for col in cursor.description]
            results = [dict(zip(columns, row)) for row in cursor.fetchall()]

            if not results:
                logger.info(f"No results found for query: {sql_query}")
                return None

            logger.info(f"Query returned {len(results)} rows.")
            return results

        except (Exception,Error) as e:
            logger.exception(f"Error executing query: {sql_query}")
            raise
        
        finally:
            if connection and connection.is_connected():
                cursor.close()
                connection.close()
                logger.debug("MySQL connection returned to pool.")

    def close_pool(self):
        self.pool = None
        logger.info("MySQL connection pool closed.")
