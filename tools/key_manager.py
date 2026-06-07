import os
import logging
from typing import List

logger = logging.getLogger(__name__)

class KeyManager:
    """
    Manages a pool of Google API keys to mitigate 429 RESOURCE_EXHAUSTED errors.
    Provides automatic rotation when a key is exhausted.
    """
    def __init__(self):
        # Load keys from comma-separated string in .env
        raw_keys = os.getenv("GOOGLE_API_KEYS", "")
        if not raw_keys:
            # Fallback to single key if pool is not defined
            self.keys = [os.getenv("GOOGLE_API_KEY")] if os.getenv("GOOGLE_API_KEY") else []
        else:
            self.keys = [k.strip() for k in raw_keys.split(",") if k.strip()]
        
        self.current_index = 0
        
        if not self.keys:
            logger.error("KeyManager: No Google API keys found in .env!")
        else:
            logger.info(f"KeyManager: Initialized with {len(self.keys)} keys.")

    def get_key(self) -> str:
        """Returns the current active key."""
        if not self.keys:
            return ""
        return self.keys[self.current_index]

    def rotate_key(self):
        """Moves to the next key in the pool."""
        if len(self.keys) <= 1:
            logger.warning("KeyManager: Rotation requested but only one key is available.")
            return
            
        self.current_index = (self.current_index + 1) % len(self.keys)
        new_key_masked = f"...{self.keys[self.current_index][-5:]}"
        logger.info(f"KeyManager: Rotated to new key: {new_key_masked}")

    def get_all_keys(self) -> List[str]:
        return self.keys

    def get_client(self):
        """
        Creates and returns a genai.Client instance.
        If GOOGLE_GENAI_USE_VERTEXAI is set to 'true', it initializes in Vertex AI mode
        using Application Default Credentials (ADC) on Google Cloud (e.g. Cloud Run service account).
        Otherwise, it falls back to the current local API key from KeyManager.
        """
        from google import genai
        if os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "false").lower() == "true":
            logger.info("KeyManager: Initializing genai.Client in Vertex AI mode using ADC.")
            return genai.Client()
        else:
            return genai.Client(api_key=self.get_key())
