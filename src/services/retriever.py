from services.configuration.config import settings
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from pinecone import Pinecone
import asyncio
from services.configuration.logger import get_logger
from fastapi import HTTPException

logger = get_logger("SchemaContextLogger")  # Renamed for clarity

pc = Pinecone(settings.PINECONE_API_KEY)
index = pc.Index(settings.INDEX_NAME)

embeddings = GoogleGenerativeAIEmbeddings(
    model="models/gemini-embedding-exp-03-07",
    task_type="semantic_similarity"
)

def semantic_search(query: str, top_k: int = 2) -> list:
    logger.info(f"Performing semantic search for query: {query}")
    try:
        query_embedding = embeddings.embed_query(query)
        logger.debug(f"Query embedding generated successfully.")

        response = index.query(
            vector=query_embedding,
            top_k=top_k,
            include_metadata=True
        )

        matches = response.get('matches', [])
        logger.info(f"Found {len(matches)} semantic matches from Pinecone.")

        return [match['metadata'] for match in matches]

    except Exception as e:
        logger.error(f"Error during semantic search: {e}")
        return []

def clean_rag_text(text: str) -> str:
    logger.debug("Cleaning RAG text.")
    cleaned = text.strip().replace('\\n', '\n').replace('\n\n', '\n')
    lines = cleaned.splitlines()

    formatted_lines = [
        f"  {line}" if line.startswith('-') else line.strip() for line in lines
    ]

    cleaned_text = '\n'.join(formatted_lines)
    logger.debug(f"Cleaned RAG text: {cleaned_text}")
    return cleaned_text

async def get_schema_context_from_rag(query: str) -> str:
    logger.info(f"Retrieving schema context for query: {query}")
    results = await asyncio.to_thread(semantic_search, query)

    combined = "\n".join(
        clean_rag_text(item['text']) for item in results if 'text' in item
    )

    if not combined.strip():
        logger.warning("No RAG schema context retrieved.")
        raise HTTPException(status_code=500, detail="Schema metadata unavailable from RAG.")

    logger.info("Successfully retrieved and cleaned schema context.")
    logger.debug(f"Schema context: {combined}")
    return combined
