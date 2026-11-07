import os
from dotenv import load_dotenv

load_dotenv()

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "luciano-qwen35")
OPENWORK_PORT = int(os.getenv("OPENWORK_PORT", "8787"))
