import os
from dotenv import load_dotenv
load_dotenv()
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.document_loaders import DirectoryLoader,TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone

loader = DirectoryLoader("./schema_text/",glob="./*.txt",loader_cls=TextLoader)
document = loader.load()

text_split = RecursiveCharacterTextSplitter(chunk_size=5000,chunk_overlap=0)
split_documents = text_split.split_documents(document)


embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-exp-03-07",task_type="semantic_similarity")

pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
docsearch = PineconeVectorStore.from_texts([t.page_content for t in split_documents], embeddings, index_name='nlsql')