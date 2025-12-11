"""
Configuration management for Voice Agent
Loads environment variables from .env files and provides centralized config access
"""

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env files
load_dotenv()


class ConfigManager:
    """Centralized configuration management for the voice agent"""

    _instance: Optional["ConfigManager"] = None

    def __init__(self):
        """Initialize configuration from environment variables"""
        # LiveKit configuration
        self.livekit_url = os.getenv("LIVEKIT_URL")
        self.livekit_api_key = os.getenv("LIVEKIT_API_KEY")
        self.livekit_api_secret = os.getenv("LIVEKIT_API_SECRET")

        # OpenAI/LLM configuration
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.llm_model = os.getenv("LLM_MODEL", "openai/gpt-4.1-nano")
        self.embedding_model = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

        # PostgreSQL configuration
        self.postgresql_url = os.getenv("POSTGRESQL_URL")

        # Qdrant Vector Database configuration
        self.qdrant_url = os.getenv("QDRANT_URL")
        self.qdrant_api_key = os.getenv("QDRANT_API_KEY")
        self.qdrant_collection = os.getenv("COLLECTION_NAME", "pt_cv")

        self.avatar_provider = os.getenv("AVATAR_PROVIDER", "none")
        # Validate required configuration
        self._validate_config()

    def _validate_config(self) -> None:
        """Validate that all required configuration is present"""
        required_vars = {
            "LIVEKIT_URL": self.livekit_url,
            "LIVEKIT_API_KEY": self.livekit_api_key,
            "LIVEKIT_API_SECRET": self.livekit_api_secret,
            "OPENAI_API_KEY": self.openai_api_key,
            "POSTGRESQL_URL": self.postgresql_url,
            "QDRANT_URL": self.qdrant_url,
            "QDRANT_API_KEY": self.qdrant_api_key,
        }

        missing = [key for key, value in required_vars.items() if not value]
        if missing:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing)}. "
                f"Please set them in .env.local"
            )

    # LiveKit getters
    def get_livekit_url(self) -> str:
        """Get LiveKit server URL"""
        return self.livekit_url

    def get_livekit_api_key(self) -> str:
        """Get LiveKit API key"""
        return self.livekit_api_key

    def get_livekit_api_secret(self) -> str:
        """Get LiveKit API secret"""
        return self.livekit_api_secret

    # LLM getters
    def get_openai_api_key(self) -> str:
        """Get OpenAI API key"""
        return self.openai_api_key

    def get_llm_model(self) -> str:
        """Get LLM model name"""
        return self.llm_model

    def get_embedding_model(self) -> str:
        """Get embedding model name"""
        return self.embedding_model

    # Database getters
    def get_postgresql_url(self) -> str:
        """Get PostgreSQL connection URL"""
        return self.postgresql_url

    def get_qdrant_url(self) -> str:
        """Get Qdrant server URL"""
        return self.qdrant_url

    def get_qdrant_api_key(self) -> str:
        """Get Qdrant API key"""
        return self.qdrant_api_key

    def get_qdrant_collection(self) -> str:
        """Get Qdrant collection name"""
        return self.qdrant_collection
    
    def get_avatar_provider(self) -> str:
        """Get Avatar provider name"""
        return self.avatar_provider

    @classmethod
    def get_instance(cls) -> "ConfigManager":
        """Get or create singleton instance"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset singleton instance (for testing)"""
        cls._instance = None


def get_config() -> ConfigManager:
    """Get the global configuration instance"""
    return ConfigManager.get_instance()


if __name__ == "__main__":
    # Simple test
    try:
        config = get_config()
        print(" Configuration loaded successfully")
        print(f"  - LiveKit URL: {config.get_livekit_url()[:20]}...")
        print(f"  - LLM Model: {config.get_llm_model()}")
        print(f"  - Qdrant Collection: {config.get_qdrant_collection()}")
    except ValueError as e:
        print(f" Configuration error: {e}")
