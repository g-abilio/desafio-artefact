import os
from dataclasses import dataclass 
from pathlib import Path 
from dotenv import load_dotenv

load_dotenv()

@dataclass(frozen=True)
class Config:
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL")
    ollama_chat_model: str = os.getenv("OLLAMA_CHAT_MODEL")