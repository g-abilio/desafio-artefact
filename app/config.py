import os
from dataclasses import dataclass 
from pathlib import Path 
from dotenv import load_dotenv

load_dotenv()

@dataclass(frozen=True)
class Config:
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    ollama_chat_model: str = os.getenv("OLLAMA_CHAT_MODEL", "llama3.1:8b")
    ollama_embedding_model: str = os.getenv("OLLAMA_EMBEDDING_MODEL", "embeddinggemma")
    data_dir: Path = Path(os.getenv("DATA_DIR", "data"))

config = Config()