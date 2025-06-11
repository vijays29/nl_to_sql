from services.configuration.config import settings
from mysql.connector import pooling, Error
from services.configuration.logger import get_logger

logger = get_logger("MysqlExecutionLogger")

class MysqlDB:
    """
    MysqlDB manages connections to a MySQL database using a connection pool.
    It supports safe execution of SQL queries and handles connection lifecycle.
    """
    def __init__(self):
        """
        Initializes the MySQL connection pool upon object creation.
        """
        self.pool = None
        self.initialize_pool()

    def initialize_pool(self):
        """
        Sets up a MySQL connection pool using parameters from the settings module.
        Ensures optimized reuse of connections for concurrent access.
        """
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
        """
        Executes a SQL query using a pooled MySQL connection.

        Parameters:
            sql_query (str): The SQL query to execute.
            params (tuple|None): Optional parameters for parameterized queries.

        Returns:
            list[dict]: Result set represented as a list of dictionaries (column-value pairs).
                        Returns None if the query yields no results.

        Raises:
            Exception/Error: If query execution fails due to connection or SQL issues.
        """
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
        """
        Closes the connection pool by dereferencing it.
        Intended to be called during application shutdown or cleanup.
        """
        self.pool = None
        logger.info("MySQL connection pool closed.")