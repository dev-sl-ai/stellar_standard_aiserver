import os
from dotenv import load_dotenv

load_dotenv(".env")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SERP_API_KEY = os.getenv("SERP_API_KEY")


