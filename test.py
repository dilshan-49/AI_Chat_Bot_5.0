import os
import time
import shutil
import json
from google.cloud import aiplatform_v1beta1 as aiplatform
from google.oauth2 import service_account
from google.cloud import dialogflowcx_v3 as dialogflow
import vertexai
import tempfile
import plotly.express as px
from vertexai.generative_models import GenerativeModel
from PyPDF2 import PdfReader
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores.chroma import Chroma
from langchain_google_vertexai import VertexAIEmbeddings
from langchain.prompts import PromptTemplate
import streamlit as st
import streamlit.components.v1 as components
import requests

# Configurations and paths
CHROMA_PATH = './chroma'
GOOGLE_APPLICATION_CREDENTIALS = './electionchatbot-config.json'
PROJECT_ID = "electionchatbot-435710"
LOCATION = 'us-central1'
AGENT_ID = "5aad9da8-085f-43d5-8d17-341f385b0e2d"
SESSION_ID = "my-session"

SAVE_PATH= './downloaded_files/'# Path to save the downloaded PDF

credentials = service_account.Credentials.from_service_account_file(GOOGLE_APPLICATION_CREDENTIALS)
access_token = credentials.token


components.html( 
    '''
    <link rel="stylesheet" href="https://www.gstatic.com/dialogflow-console/fast/df-messenger/prod/v1/themes/df-messenger-default.css">
<script src="https://www.gstatic.com/dialogflow-console/fast/df-messenger/prod/v1/df-messenger.js"></script>
<df-messenger
  oauth-client-id="{access_token}"
  location="us-central1"
  project-id="electionchatbot-435710"
  agent-id="5aad9da8-085f-43d5-8d17-341f385b0e2d"
  language-code="en"
  max-query-length="-1">
  <df-messenger-chat
   chat-title="Election Chat Bot Agent">
  </df-messenger-chat>
</df-messenger>
<style>
  df-messenger {
    z-index: 999;
    position: fixed;
    bottom: 0;
    right: 0;
    top: 0;
    width: 350px;
  }
</style>'''
)

# Initialize the Vertex AI client
def init_vertex_ai():
    aiplatform.init(project=PROJECT_ID, location=LOCATION, credentials=credentials)
    client_options = {"api_endpoint": "us-central1-aiplatform.googleapis.com"}  # Replace with the correct region
    client = aiplatform.services.conversation_service.ConversationsClient(credentials=credentials, client_options=client_options)
    return client


# Initialize Dialogflow session client
def init_dialogflow_client(credentials):
    session_client = dialogflow.SessionsClient(credentials=credentials )
    return session_client

# Function to detect intent (i.e., query the Dialogflow agent)
def detect_intent_text(session_client, project_id, session_id, text, language_code='en-US'):
    session = session_client.session_path(project_id, session_id )

    text_input = dialogflow.types.TextInput(text=text, language_code=language_code)
    query_input = dialogflow.types.QueryInput(text=text_input)


    response = session_client.detect_intent(session=session, query_input=query_input)

    return response.query_result.fulfillment_text
