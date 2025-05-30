from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from services.chat_agent import Chat_agent
from services.mysql_executer import MysqlDB
from services.configuration.keywords import Contains_Forbidden_Keywords
from services.configuration.logger import get_logger
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
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
        logger.info("Aggregation detected in SQL query. Skipping pagination.")
        return generated_sql
    logger.info(f"Applying pagination: LIMIT {limit} OFFSET {offset}")
    return f"{generated_sql} LIMIT {limit} OFFSET {offset}"

@app.post("/data-requests")
async def process_request(request: NlQueryRequest):
    logger.info("Received new data request.")
    user_query = request.user_query.strip()
    requested_limit = min(request.limit, MAX_LIMIT)

    logger.debug(f"User query: {user_query}")
    logger.debug(f"Offset: {request.offset}, Requested limit: {request.limit}, Enforced limit: {requested_limit}")

    if Contains_Forbidden_Keywords(user_query):
        logger.warning("Query contains forbidden DML/DCL/DDL keywords.")
        raise HTTPException(
            status_code=400,
            detail="Your query contains restricted terms related to database modifications, which are not allowed."
            )

    if not user_query:
        logger.warning("Received an empty query request.")
        raise HTTPException(status_code=400, detail="Query cannot be empty. Please enter a valid query.")

    generated_sql = await chat.nl_to_sql(user_query)

    if not generated_sql:
        logger.warning(f"Failed to generate SQL for query: {user_query}")
        raise HTTPException(status_code=400, detail="Quota exceeded. Please check your plan and billing details.")
    logger.info(f"Generated SQL query: {generated_sql}")
    sql_query = format_sql_query(generated_sql, request.offset, requested_limit)
    query_result = db_instance.Execute_Query(sql_query)
    logger.info("Successfully fetched and sent query results.")
    return jsonable_encoder(query_result)

if __name__ == "__main__":
    logger.info("Starting FastAPI server on 0.0.0.0:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)