import os
from dotenv import load_dotenv

load_dotenv(".env")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SERP_API_KEY = os.getenv("SERP_API_KEY")

# Azure Speech — key stays server-side only; clients fetch a short-lived token via /api/azure-token.
AZURE_SPEECH_KEY = os.getenv("AZURE_SPEECH_KEY")
AZURE_SPEECH_REGION = os.getenv("AZURE_SPEECH_REGION", "japaneast")

