import os
import time
import pickle
from google.cloud import storage, aiplatform
from google.oauth2 import service_account
import vertexai
from langchain.vectorstores.chroma import Chroma
from langchain_google_vertexai import VertexAIEmbeddings
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from vertexai.generative_models import GenerativeModel
from google.api_core.exceptions import ResourceExhausted
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
# Configuration
GOOGLE_APPLICATION_CREDENTIALS = './vertexAIconfig.json'
PROJECT_ID = "electionchatbot-435710"
BUCKET_NAME = "election-bot"
EMBEDDINGS_BLOB_NAME = "manifesto_embeddings.pkl"
CHROMA_PERSIST_DIRECTORY = "./chroma_db"
LOCATION = 'us-central1'


# Initialize Google Cloud Storage client
storage_client = storage.Client.from_service_account_json(GOOGLE_APPLICATION_CREDENTIALS)
bucket = storage_client.bucket(BUCKET_NAME)
credentials = service_account.Credentials.from_service_account_file(GOOGLE_APPLICATION_CREDENTIALS)
aiplatform.init(project=PROJECT_ID, location=LOCATION, credentials=credentials)
vertexai.init(project=PROJECT_ID, location=LOCATION)

def load_and_split_pdfs(pdf_files):
    # Open the PDF file
    with open(file_path, 'rb') as file:
        # Create a PdfFileReader object
        pdf_reader = PyPDF2.PdfFileReader(file)
        
        # Get the number of pages
        num_pages = pdf_reader.numPages
        
        # Initialize a variable to store the extracted text
        text = []
        
        # Loop through each page and extract text
        for page_num in range(num_pages):
            page = pdf_reader.getPage(page_num)
            text.extend(page.extract_text())
    
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=100,
        length_function=len,
        add_start_index=True
    )
    chunks = text_splitter.split_documents(text)
    return chunks

def create_embeddings(chunks):
    vertex_embeddings = VertexAIEmbeddings(model_name="textembedding-gecko@003")
    
    # Create and persist Chroma database
    db = Chroma.from_documents(
        chunks, vertex_embeddings, persist_directory=CHROMA_PERSIST_DIRECTORY, collection_name="survey"
    )
    db.persist()
    return db


# Usage in your main application
def main():
    pdf_files = "Binder1.pdf"  # List of your PDF files
    load_and_split_pdfs(pdf_files)
    
    # Process results...

if __name__ == "__main__":
    main()