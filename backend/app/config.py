import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    GEMINI_API_KEY: str = Field(default="", description="Google Gemini API Key")
    GEMINI_MODEL: str = Field(default="gemini-2.5-flash", description="Gemini model identifier")
    
    PORT: int = 8000
    HOST: str = "0.0.0.0"
    CORS_ORIGINS: str = Field(
        default="http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173,http://localhost:4173,http://127.0.0.1:4173,*",
        description="Comma-separated list of allowed CORS origins, or * for all"
    )
    
    # Storage paths
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    STORAGE_DIR: str = Field(default="")
    DATABASE_PATH: str = Field(default="")
    CHROMA_PERSIST_DIR: str = Field(default="")
    
    # Retrieval Configuration
    EMBEDDING_PROVIDER: str = Field(default="onnx_minilm", description="Embedding provider: onnx_minilm or local_fast")
    SIMILARITY_THRESHOLD: float = Field(default=0.50, description="Minimum cosine similarity required for evidence relevance")
    
    MAX_FILE_SIZE_MB: int = 25
    ALLOWED_EXTENSIONS: list[str] = [".pdf"]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.STORAGE_DIR:
            self.STORAGE_DIR = os.environ.get("STORAGE_DIR", os.path.join(self.BASE_DIR, "storage"))
        if not self.DATABASE_PATH:
            self.DATABASE_PATH = os.environ.get("DATABASE_PATH", os.path.join(self.STORAGE_DIR, "proofmind.db"))
        if not self.CHROMA_PERSIST_DIR:
            self.CHROMA_PERSIST_DIR = os.environ.get("CHROMA_PERSIST_DIR", os.path.join(self.STORAGE_DIR, "chroma_db"))
            
        os.makedirs(self.STORAGE_DIR, exist_ok=True)
        os.makedirs(self.CHROMA_PERSIST_DIR, exist_ok=True)

settings = Settings()
