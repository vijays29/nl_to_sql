
# NL-to-SQL API Service

## Overview
A FastAPI-based service that converts natural language queries into SQL SELECT statements via a Gemini-powered agent and executes them safely on MySQL. It supports schema-aware generation using RAG, pagination, and filters out dangerous SQL commands.


## Features
- **Natural Language** → SQL: Uses Gemini (via langchain_google_genai) to generate SELECT-only queries.

- **Schema safety**: RAG retrieval of schema context ensures generated SQL respects actual database metadata.

- **Pagination**: Applies LIMIT/OFFSET client-side when no aggregation is used.

- **Security filters**: Blocks DML/DCL/DDL (e.g. INSERT, DROP, UPDATE) in user queries via forbidden keyword checks.

- **Connection pooling**: Manages MySQL connections via mysql.connector.pooling.

- **Logging**: Structured with custom logger to capture API and SQL agent behavior.

- **CORS support**: Allowing POSTs from configured origins.
## Environment setup & Prerequisites

### **1. Gemini (Google Generative AI) API Key Setup**

 **Step-by-Step:**

  1 . Visit: https://makersuite.google.com/app/apikey

  2 . Sign in with your Google account.

  3 . Click **“Create API Key”**.

  4 . Copy the generated API key.

**Add to** `.env`:
```bash
API_KEY=your_google_generative_ai_api_key_here
```
### **2. Create Google Service Account**

If you need a service account for accessing Google Cloud resources (e.g., BigQuery, GCS, etc.):

**Step-by-Step:**

 1 . Go to: https://console.cloud.google.com/

 2 . Navigate to **IAM & Admin > Service Accounts**.

 3 . Click **“Create Service Account”**:

 - Name: e.g., `my-api-service`

 - Role: Select appropriate role (e.g., `Owner`, or custom role based on permissions required).

 - After creation, go to the service account and click **“Keys”** → **“Add Key”** → **“Create new key”** → Choose `JSON` → Download the key file.

**Save the credentials:**

Place the downloaded JSON key in your project directory, and set the path in your environment:
```bash
GOOGLE_APPLICATION_CREDENTIALS=path/to/your-service-account.json
```
### **3. Pinecone Index Creation Procedure**
**Step-by-Step:**

#### Step 1: Sign Up / Log in
 - Visit: https://www.pinecone.io/

 - Create an account and log in.

#### Step 2: Create Index
   1 . Go to https://app.pinecone.io/

   2 . Click **“Create Index”**

   3 . Fill in details:

- **Index Name**: e.g., `nl2sql`

- **Dimension**: match your embedding model (e.g., `3072`)

- **Metric**: `cosine`


#### Step 3: Get API Key and Environment
 - After creating index, go to API Keys tab. Copy API Key

**Add to** `.env`:
```bash
PINECONE_API_KEY=your_pinecone_api_key
INDEX_NAME=nl2sql
```
## Prerequisites
- Python 3.9+
- MySQL database accessible with provided credentials
- A Pinecone index populated with schema embeddings
- `.env` containing:
```bash
API_KEY=<Gemini API key>
HOST_NAME=<MySQL host>
USER_NAME=<MySQL user>
PASSWORD=<MySQL password>
DATABASE_NAME=<MySQL database>
POOL_NAME=<pool name>
POOL_SIZE=<number>
PINECONE_API_KEY=<pinecone key>
INDEX_NAME=<pinecone index name>
```
## Project Structure
```bash
src/
├── services/
│   ├── configuration/
│   │   ├── schema_text/
│   │   ├── config.py
│   │   ├── keywords.py
│   │   ├── logger.py
│   │   ├── vector.py
│   ├── chat_agent.py
│   ├── mysql_executer.py
│   ├── retriever.py
├── app.py
.env
.gitignore
requirements.txt
```

| File/Folder         | Description                                                    |
| ------------------- | -------------------------------------------------------------- |
| `app.py`            | Main FastAPI application entry point                           |
| `services/`         | Contains core logic and services                               |
| `chat_agent.py`     | Handles the NL-to-SQL conversion logic                         |
| `mysql_executer.py` | Executes generated SQL queries on MySQL                        |
| `retriever.py`      | Likely supports semantic or keyword-based data retrieval       |
| `configuration/`    | Configuration helpers and utilities                            |
| `config.py`         | Environment or global configuration settings                   |
| `logger.py`         | Logging setup for the application                              |
| `vector.py`         | Vector-related utilities (e.g., embeddings or semantic search) |
| `keywords.py`       | Keyword filtering or forbidden terms logic                     |
| `schema_text/`      | Likely contains schema-specific configurations                 |
| `.env`              | Environment variables file                                     |
| `requirements.txt`  | Lists all dependencies for the project                         |
| `.gitignore`        | Specifies which files/folders to ignore in version control     |

## Installation
```bash
git clone https://github.com/vijays29/nl_to_sql.git
cd nl_to_sql
python -m venv myworld
source myworld/bin/activate
pip install -r requirements.txt
```
#### requirements.txt should include:
 - fastapi
 - uvicorn
 - pydantic
 - mysql-connector-python
 - google-generative-ai
 - langchain, langchain-google-genai
 - pinecone-client
 - python-dotenv
## Running the Server
```bash
python3 app.py
```
API will be available at `http://0.0.0.0:8000`.
##  Endpoints
**POST** `/data-requests`

#### Request
```json
{
  "user_query": "i need all point order",
  "offset": 0,
  "limit": 10
}
```
### Behavior

 - Rejects if forbidden keywords are present (INSERT, DROP, etc.).

 - Converts NL input to SQL via Gemini using provided schema context.

 - Applies pagination unless aggregation keywords are detected.

 - Executes the SQL and retrieves results + total count.

 - Returns JSON with data, data_length, and status.

### Responses(Example)

- **SUCCESS**: includes actual data
```json
{
"data_length": 2032,
"data": [
{
"DTYPE": "POINT_TASK",
"TASK_ID": "170000",
"TASK_STATE": "ACTIVATED",
"TASK_STATUS": "CLOSED",
"TASK_NAME": "ProvTask-RES-REQD",
"TASK_TYPE": "Task",
"CATEGORY": null,
"COMPLETED_DATE": "2025-03-14T10:53:37.982000",
"CUSTOMER_SEGMENT": "INTERNAL",
"DOMAIN": "ip",
"CREATED_DATE": "2025-03-14T10:53:35.159000",
"DESIGN_WITH_ONLY_CONSTRAINT": 1,
"INTERNAL_ORDER_ID": "938",
"LAST_MODIFIED_DATE": "2025-03-14T10:53:37.982000",
"ORDER_SUB_TYPE": "New",
"ORDER_TYPE": "INTERNAL",
"ROOT_ORDER_LINE_ID": "9392",
"SERVICE_TYPE": "587",
"SFP_CONSTRAINT_STATE": "VPN MPLS Product",
…
},
...
]
,
"status": "SUCCESS"
}
```

- **FAILED**: explains reasons (raw SQL error, forbidden content, etc.)
```json
{
"data_length": 0,
"data": [],
"response": "Your query contains restricted terms related to database
modifications, which are not allowed.",
"status": "FAILED"
}
```
## Security & Limitations
 - **DML/DDL protection**: Filters common SQL commands using Contains_Forbidden_Keywords.
 - **SELECT-only policy**: Chat_agent enforces “SELECT‑only” and strict adherence to schema; rejects invalid requests.
- **Pagination control**: Offloaded to API—ensures the LLM doesn’t manipulate LIMIT/OFFSET.
## Conclusion

This project successfully demonstrates a secure and intelligent natural language to SQL query system using FastAPI, Gemini (via LangChain), and MySQL. It bridges the gap between human language and database interaction by allowing non-technical users to retrieve structured data insights through plain English queries.

By combining Retrieval-Augmented Generation (RAG) for schema awareness and strict SQL validation layers, the system ensures safety, relevance, and performance. It is modular, scalable, and integrates well with frontend dashboards through API responses that support pagination and real-time feedback.

This implementation lays a strong foundation for future enhancements such as:

 - Expanding to multiple database types (e.g., PostgreSQL, Oracle)

 - Role-based query access controls

 - Query caching or logging for analytics

 - UI-integrated autocomplete suggestions for user queries

Overall, this solution aligns with modern AI-assisted data access needs, emphasizing both **usability** and **security**.
## Contributing

We welcome contributions to improve this chatbot project!  
Feel free to **fork the repository**, make your changes, and submit a **pull request** with any enhancements or bug fixes.

## Contact

For inquiries or support, feel free to reach out to:

- [Vijay S](vijays003729@gmail.com)
