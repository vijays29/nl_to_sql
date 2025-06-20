import asyncio
import re
import google.generativeai as Aimodel
from services.configuration.config import settings
from langchain.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.runnables import (RunnablePassthrough, RunnableLambda)
from services.configuration.logger import get_logger
from services.retriever import get_schema_context_from_rag
from google.api_core.exceptions import GoogleAPIError

# Initialize logger specific to Chat Agent activities
logger = get_logger("ChatAgentLogger")

# Configure the Gemini API with the provided API key
api_key = settings.API_KEY
Aimodel.configure(api_key=api_key)

def clean_sql_query(query: str) -> str:
    """
    Cleans the generated SQL query by removing backticks and `sql` tokens.
    Returns the trimmed query string.
    """
    logger.debug(f"Cleaning SQL query: {query}")
    query_cleaned = re.sub(r'`|sql', '', query, flags=re.IGNORECASE)  
    return query_cleaned.strip()

class Chat_agent:
    """
    Chat_agent acts as an interface to convert natural language queries into SQL
    using Google's Gemini language model via LangChain.
    """
    def __init__(self):
        """
        Initializes the chat agent with Gemini 2.0 Flash model configured to respond deterministically.
        """
        logger.info("Initializing Chat agent with Gemini model.")
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            api_key=api_key,
            temperature=0 # Zero temperature for consistent outputs
        )
        logger.info("Model initialized successfully.")
    
    async def nl_to_sql(self,user_query: str) -> str | None:
        """
        Converts a natural language query into a valid SQL SELECT statement.
        
        Steps:
        - Fetch schema context using RAG mechanism.
        - Format the prompt with strict SQL generation rules.
        - Use LangChain to pass prompt to Gemini model.
        - Clean and validate the output SQL.
        
        Returns:
        - SQL SELECT query string if valid.
        - None if the model generates invalid or non-compliant SQL.
        """
        logger.info(f"Received user query: '{user_query}'")

        try:
            # Retrieve relevant table and column schema context based on user query
            logger.debug("Fetching schema context from RAG for the query.")
            schema_context = await get_schema_context_from_rag(user_query)

            # Prompt template defining strict SQL generation rules
            prompt_template = PromptTemplate(
                input_variables=["user_query", "schema_context"],
                template="""
                    You are a highly skilled SQL query generation tool designed for Mysql enterprise database environments. 
                    Your sole function is to translate natural language requests into valid and efficient SQL SELECT statements. 
                    Adhere strictly to the following rules, and respond ONLY with the generated SQL query.
                    Any deviation from these rules will result in an error.

                    **Mandatory Rules:**

                    1. **SELECT-Only Operations:**
                    * Your output MUST be a valid SQL SELECT statement, and ONLY a SELECT statement.
                    * Any request implying data modification (DML, DDL, TCL, DCL) should result in the immediate response: `"ERROR"`.

                    2. **Explicit Column Specification & Handling 'All Tables' Requests:**  
                    * If the user specifies column names, include only those columns in the `SELECT` statement.  
                    * If the user requests "all columns," "all data," or does not specify columns, use `SELECT *`. 
                    * If the user requests "all tables,return `"ERROR" 
                    * If no tables exist, return `"ERROR"`.

                    3. **Schema Adherence & Validation:**  
                    * Use only table and column names provided in the schema.  
                    * If the user requests a non-existent table or column, return `"ERROR"`.

                    4. **Handling Columns Appearing in Multiple Tables:**
                    * If a column exists in multiple tables, return a `UNION ALL` query selecting that column from each table.
                    * The result should include a new column indicating the source table name.
                
                    5. **Precise Filtering & Conditions:**
                    * Translate all WHERE clause conditions precisely as stated.
                    * Ensure accurate handling of date ranges (using appropriate date/time functions if needed), numerical comparisons, and string matching (using LIKE or other relevant functions as needed).

                    6. **Aggregation and Ordering Implementation:**
                    * Correctly implement requested aggregation functions (COUNT) only.
                    * Implement ORDER BY clauses exactly as requested, including the specified column(s) and sort order (ASC or DESC). Default to ASC if not specified.

                    7. **Pagination is Strictly Prohibited (LIMIT, OFFSET, FETCH):**
                    * Your output MUST NOT include:
                        * `LIMIT`
                        * `OFFSET`
                        * `FETCH NEXT … ROWS ONLY`
                    * If a user requests any form of pagination, return `"ERROR"`

                    8. **Zero Tolerance for Additional Text:**
                    * Your output consists SOLELY of the generated SQL SELECT statement. Do NOT include any explanations, comments, or introductory text. Failure to adhere to this is an error.

                    9. **Assume Correct Grammar:**
                    * Assume that the user input is grammatically correct, though it might contain synonyms or multiple ways to ask the same question.

                    **Process:**

                    1. Receive a natural language request.
                    2. Parse the request to identify:
                    * The target table(s).
                    * The desired columns.
                    * Any filtering conditions (WHERE clause).
                    * Any aggregation requirements.
                    * Any sorting requirements (ORDER BY clause).
                    * Any LIMIT/OFFSET requirements (which MUST NOT be included in the query).
                    3. Construct a valid SQL SELECT statement that fulfills all requirements.
                    4. If a requested column appears in multiple tables, construct a `UNION ALL` query with a `source_table` column..
                    5. If the user asks for data from **both tables with a relationship**, construct an appropriate `JOIN` query.
                    6. Output ONLY the SQL SELECT statement. If any rule is violated, output `"ERROR"`.
                    7. point_order table and point_task table 
                    8. ORDER_ID in POINT_ORDER and POINT_TASK table same, you can create join query basis this. (e.g:SELECT * FROM POINT_TASK INNER JOIN POINT_ORDER ON POINT_TASK.ORDER_ID = POINT_ORDER.ORDER_ID
                    
                    Schema:Generated SQL:
                    {schema_context}

                    Now convert the following Natural Language Query:
                    {user_query}""")
            
            # Define LangChain flow for chaining input, prompt, LLM, and post-processing
            chain = (
                {"user_query": RunnablePassthrough(), "schema_context": RunnableLambda(lambda _: schema_context)}
                | prompt_template
                | self.llm
                | RunnableLambda(lambda x: x.content)
                )
            
            # Run the chain in a separate thread to avoid blocking
            logger.debug("Invoking LLM chain to generate SQL query.")
            sql_query = await asyncio.to_thread(chain.invoke, user_query)

            # Clean unwanted tokens and whitespace from query
            sql_query = clean_sql_query(sql_query)

            # Remove trailing semicolon for formatting consistency
            if sql_query.endswith(';'):
                sql_query = sql_query[:-1]
                logger.info("Removed semicolon from generated SQL.")
            else:
                logger.info("No semicolon found in generated SQL.")

            # Final validation: Ensure SQL is a valid SELECT and not an error message
            if "ERROR" in sql_query or not sql_query.lower().startswith("select"):
                logger.warning(f"Invalid SQL generated: {sql_query}")
                return None
        
            logger.info(f"Generated valid SQL: {sql_query}")
            return sql_query
        
        # Log and raise any failure during the generation process
        except (Exception,GoogleAPIError) as e:
            logger.exception(f"SQL generation failed for query '{user_query}': {e}")
            raise