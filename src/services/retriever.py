from services.configuration.config import settings
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from pinecone import Pinecone
import asyncio
from services.configuration.logger import get_logger

logger = get_logger("SchemaRetrievalLogger") 

class SemanticSearchHelper:
    def __init__(self):
        self.pc = Pinecone(settings.PINECONE_API_KEY)
        self.index = self.pc.Index(settings.INDEX_NAME)

        self.embeddings = GoogleGenerativeAIEmbeddings(
            model="models/gemini-embedding-exp-03-07",
            task_type="semantic_similarity"
        )

    def semantic_search(self, query: str, top_k: int = 4) -> list:
        try:
            logger.debug(f"Embedding query for semantic search: {query}")
            query_embedding = self.embeddings.embed_query(query)

            response = self.index.query(
                vector=query_embedding,
                top_k=top_k,
                include_metadata=True
            )

            matches = response.get('matches', [])
            logger.info(f"Found {len(matches)} results from Pinecone for query: '{query}'")

            return [match['metadata'] for match in matches]

        except Exception as e:
            logger.error(f"Error during semantic search for query '{query}': {e}")
            return []

    @staticmethod
    def clean_rag_text(text: str) -> str:
        cleaned = text.strip().replace('\\n', '\n').replace('\n\n', '\n')
        lines = cleaned.splitlines()

        formatted_lines = [
            f"  {line}" if line.startswith('-') else line.strip() for line in lines
        ]

        cleaned_text = '\n'.join(formatted_lines)
        return cleaned_text


async def get_schema_context_from_rag(query: str) -> str:
    helper = SemanticSearchHelper()

    logger.info(f"Starting retrieval of schema context for query: '{query}'")
    results = await asyncio.to_thread(helper.semantic_search, query)

    combined = "\n".join(
        helper.clean_rag_text(item['text']) for item in results if 'text' in item
    )

    if not combined.strip():
        logger.warning(f"No relevant schema context found for query: '{query}'.")
        return []

    logger.info(f"Successfully retrieved schema context for query: '{query}'.")
    return combined
