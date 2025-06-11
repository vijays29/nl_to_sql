from configuration.config import settings
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone
from services.configuration.logger import get_logger

# Initialize logger for document processing
logger = get_logger("document_processing")

# Initialize Pinecone client with the provided API key
logger.info("Initializing Pinecone with API key.")
pc = Pinecone(api_key=settings.PINECONE_API_KEY)

# Load all text documents from the specified directory using TextLoader
logger.info("Loading documents from directory './schema_text/'.")
loader = DirectoryLoader(
    "./schema_text/",             # Path to directory containing schema text files
    glob="./*.txt",               # Pattern to match only .txt files
    loader_cls=TextLoader         # Class to use for loading text files
)
document = loader.load()          # Load all matched documents

# Split loaded documents into smaller chunks for better embedding performance
logger.info("Splitting documents into chunks.")
text_split = RecursiveCharacterTextSplitter(
    chunk_size=5000,              # Maximum size of each text chunk
    chunk_overlap=0               # No overlap between chunks
)
split_documents = text_split.split_documents(document)

# Initialize the Google Generative AI Embeddings model for semantic vector generation
logger.info("Initializing Google Generative AI embeddings model.")
embeddings = GoogleGenerativeAIEmbeddings(
    model="models/gemini-embedding-exp-03-07",  # Specific Gemini embedding model
    task_type="semantic_similarity"             # Use case for semantic search
)

# Create a Pinecone vector store and upload the split document embeddings
logger.info("Creating Pinecone vector store.")
docsearch = PineconeVectorStore.from_texts(
    [t.page_content for t in split_documents],  # Extract text content from each chunk
    embeddings,                                 # Embedding model to vectorize text
    index_name='nlsql'                          # Pinecone index name where vectors will be stored
)

# Completion log
logger.info("Document processing completed successfully.")