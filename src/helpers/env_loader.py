import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent.parent / ".env")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")



