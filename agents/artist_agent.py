import logging
import base64
import time
from google import genai
from google.genai import types
from typing import Dict, Optional
from tools.key_manager import KeyManager

logger = logging.getLogger(__name__)

class ArtistAgent:
    """
    The Artist Agent: Uses Google Imagen models to generate high-fidelity,
    clean architectural maps and site plans.
    """

    def __init__(self, key_manager: KeyManager):
        self.key_manager = key_manager
        self.client = self.key_manager.get_client()
        # Fast variant has higher quota and lower latency
        self.primary_model = "imagen-4.0-fast-generate-001"
        self.fallback_model = "imagen-4.0-fast-generate-001"

    def _refresh_client(self):
        """Re-instantiates the genai Client with the current key from KeyManager."""
        self.client = self.key_manager.get_client()

    def generate_map(self, scenario: str, prompt_template: str) -> Dict:
        """
        Calls Google Imagen with retries, fallback to stable models, and key rotation.
        """
        prompt = prompt_template.replace("{SCENARIO}", scenario)
        
        # Try Primary Model (Imagen 4.0)
        res = self._call_imagen(self.primary_model, prompt, scenario)
        
        # If primary fails with transient/quota issues, try Fallback
        if res['status'] == 'error' and any(err in res['message'] for err in ["503", "UNAVAILABLE", "Resource exhausted", "429"]):
            logger.warning(f"ArtistAgent: Primary model {self.primary_model} hit issues. Falling back to {self.fallback_model}...")
            res = self._call_imagen(self.fallback_model, prompt, scenario)
            
        return res

    def _call_imagen(self, model_name: str, prompt: str, scenario: str) -> Dict:
        max_retries = 2
        base_delay = 2

        for attempt in range(max_retries + 1):
            logger.info(f"ArtistAgent: Calling {model_name} for '{scenario}' (Attempt {attempt + 1})")
            try:
                response = self.client.models.generate_images(
                    model=model_name,
                    prompt=prompt,
                    config=types.GenerateImagesConfig(
                        number_of_images=1,
                        include_rai_reason=True,
                        aspect_ratio="1:1"
                    )
                )
                
                if not response.generated_images:
                    if attempt < max_retries:
                        time.sleep(base_delay * (2 ** attempt))
                        continue
                    return {"status": "error", "message": f"{model_name} returned no images"}
                    
                generated_image = response.generated_images[0]
                raw_binary = generated_image.image.image_bytes
                
                if not raw_binary:
                    return {"status": "error", "message": f"No image bytes returned from {model_name}"}

                b64_data = base64.b64encode(raw_binary).decode('utf-8')
                image_url = f"data:image/png;base64,{b64_data}"

                return {
                    "status": "success",
                    "image_url": image_url,
                    "raw_binary": raw_binary,
                    "model_used": model_name
                }

            except Exception as e:
                error_str = str(e)
                logger.error(f"ArtistAgent Error with {model_name}: {error_str}")
                
                # If Resource Exhausted or 429, Rotate Key and retry
                if any(err in error_str for err in ["Resource exhausted", "429"]) and attempt < max_retries:
                    logger.warning("ArtistAgent: Quota exhausted. Rotating API Key and retrying...")
                    self.key_manager.rotate_key()
                    self._refresh_client()
                    time.sleep(1) # Small pause for key propagation
                    continue

                if any(err in error_str for err in ["503", "UNAVAILABLE"]) and attempt < max_retries:
                    time.sleep(base_delay * (2 ** attempt))
                    continue
                
                return {"status": "error", "message": f"{model_name} Failed: {error_str}"}
