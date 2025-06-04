from configuration.config import settings
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.document_loaders import DirectoryLoader,TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone
from services.configuration.logger import get_logger

logger = get_logger("document_processing")

logger.info("Initializing Pinecone with API key.")
pc = Pinecone(api_key=settings.PINECONE_API_KEY)

logger.info("Loading documents from directory './schema_text/'.")
loader = DirectoryLoader("./schema_text/",glob="./*.txt",loader_cls=TextLoader)
document = loader.load()

logger.info("Splitting documents into chunks.")
text_split = RecursiveCharacterTextSplitter(chunk_size=5000,chunk_overlap=0)
split_documents = text_split.split_documents(document)

logger.info("Initializing Google Generative AI embeddings model.")
embeddings = GoogleGenerativeAIEmbeddings(
    model="models/gemini-embedding-exp-03-07",
    task_type="semantic_similarity"
    )

logger.info("Creating Pinecone vector store.")
docsearch = PineconeVectorStore.from_texts(
    [t.page_content for t in split_documents],
      embeddings, index_name='nlsql'
      )

logger.info("Document processing completed successfully.")