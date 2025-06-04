import re
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.responses import JSONResponse
from services.chat_agent import Chat_agent
from services.mysql_executer import MysqlDB
from services.configuration.keywords import Contains_Forbidden_Keywords
from services.configuration.logger import get_logger
from fastapi.middleware.cors import CORSMiddleware
from fastapi.encoders import jsonable_encoder
from contextlib import asynccontextmanager

logger = get_logger("API_Logger")
chat = Chat_agent()
db_instance = MysqlDB()

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up...")
    yield
    db_instance.close_pool()
    logger.info("Shutdown complete, connection pool closed.")

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["POST"],
    allow_headers=["*"],
)

class NlQueryRequest(BaseModel):
    user_query: str
    offset: int = 0
    limit: int = 10

MAX_LIMIT = 10
AGGREGATE_KEYWORDS = ["COUNT", "AVG", "SUM", "MIN", "MAX", "TOTAL"]

def format_sql_query(generated_sql: str, offset: int, limit: int) -> str:
    if any(keyword in generated_sql.upper() for keyword in AGGREGATE_KEYWORDS):
        logger.debug("Aggregation detected, skipping pagination.")
        return generated_sql
    
    logger.debug(f"Applying pagination with LIMIT {limit} and OFFSET {offset}.")
    return f"{generated_sql} LIMIT {limit} OFFSET {offset}"

@app.post("/data-requests")
async def process_request(request: NlQueryRequest):
    logger.info(f"Received request: {request.user_query[:50]}...")
    user_query = request.user_query.strip()
    requested_limit = min(request.limit, MAX_LIMIT)

    logger.debug(f"User query: {user_query}")
    logger.debug(f"Offset: {request.offset}, Limit: {requested_limit}")

    if Contains_Forbidden_Keywords(user_query):
        logger.warning("Query contains forbidden keywords (DML/DCL/DDL).")
        return JSONResponse(content={
                "Data length": 0,
                "data": [],
                "response": "Your query contains restricted terms related to database modifications, which are not allowed.",
                "status": "FAILED"
            })
    
    try:
        generated_sql = await chat.nl_to_sql(user_query)
        if not generated_sql:
            logger.warning("Failed to generate valid SQL for the given query.")
            return JSONResponse(content={
            "data_length": 0,
            "data": [],
            "response": "Failed to process input into valid SQL.",
            "status": "FAILED"
        })
        
        logger.info(f"Generated SQL query: {generated_sql[:100]}...") 
    except Exception as e:
        logger.exception("Error in SQL generation.")
        return JSONResponse(content={
        "data_length": 0,
        "data": [],
        "response": "SQL generation failed due to resource exhaustion or other issues.",
        "status": "FAILED"
    })

    try:
        sql_query = format_sql_query(generated_sql, request.offset, requested_limit)
        query_result = db_instance.Execute_Query(sql_query)
        if sql_query:
            match = re.search(r'FROM\s+([a-zA-Z0-9_]+)', sql_query, re.IGNORECASE)
            table_name = match.group(1)
            count = db_instance.Execute_Query(f"SELECT COUNT(*) FROM {table_name}")
            data_length = count[0]["COUNT(*)"]

        if not generated_sql:
            logger.warning(f"No data found for query: {sql_query}")
            return JSONResponse(content={
            "data_length": 0,
            "data": [],
            "response": "No data found for the given query.",
            "status": "FAILED"
        })
    
        logger.info("Successfully fetched query results.")
        return JSONResponse(content={
        "data_length": data_length,
        "data": jsonable_encoder(query_result),
        "status": "SUCCESS"
    })
    except Exception as e:
       logger.exception("Error executing the MySQL query.")
       return JSONResponse(content={
        "data_length": 0,
        "data": [],
        "response": "Error executing the MySQL query.",
        "status": "FAILED"
    })

if __name__ == "__main__":
    logger.info("Starting FastAPI server on 0.0.0.0:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)