import os
import requests
import uuid
import logging
import base64
import json
import time
from google import genai
from google.genai import types
from typing import Dict
from tools.key_manager import KeyManager

logger = logging.getLogger(__name__)

class AudioEngine:
    """
    The Audio Engine: Manages TTS synthesis via Google Cloud TTS and 
    forensic word-alignment via Gemini 2.5 Flash Multimodal.
    """

    def __init__(self, key_manager: KeyManager, upload_dir: str):
        self.key_manager = key_manager
        self.upload_dir = upload_dir
        self._refresh_client()
        os.makedirs(self.upload_dir, exist_ok=True)

    def _refresh_client(self):
        """Re-instantiates the genai Client with the current key from KeyManager."""
        self.client = self.key_manager.get_client()

    def generate_karaoke_audio(self, script: str) -> Dict:
        """
        1. Generates TTS audio using Google Cloud TTS API (trimmed to first 65 words for speed).
        2. Generates word-level timestamps via Gemini 2.5 Flash (Multimodal).
        """
        # CRITICAL PERFORMANCE ENHANCEMENT: Limit audio synthesis and word-alignment to the first 65 words (~20 seconds of speech) to drastically reduce TTS and Gemini alignment latency!
        words_list = script.split()
        trimmed_script = " ".join(words_list[:65]) if len(words_list) > 65 else script

        filename = f"audio_{uuid.uuid4().hex[:8]}.mp3"
        filepath = os.path.join(self.upload_dir, filename)

        max_retries = 3
        base_delay = 2

        for attempt in range(max_retries + 1):
            try:
                # 1. Google Cloud TTS (REST via Service Account OAuth2 Authentication)
                try:
                    import google.auth
                    from google.auth.transport.requests import Request
                    
                    # Set credentials path defensively if the file exists
                    if os.path.exists("google-credentials.json"):
                        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "google-credentials.json"
                    credentials, project_id = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
                    credentials.refresh(Request())
                    
                    tts_url = "https://texttospeech.googleapis.com/v1/text:synthesize"
                    headers = {
                        "Authorization": f"Bearer {credentials.token}",
                        "Content-Type": "application/json"
                    }
                    tts_payload = {
                        "input": {"text": trimmed_script},
                        "voice": {"languageCode": "en-US", "name": "en-US-Journey-F"}, # Premium studio-quality neural voice
                        "audioConfig": {"audioEncoding": "MP3"}
                    }
                    tts_res = requests.post(tts_url, json=tts_payload, headers=headers)
                except Exception as gcp_err:
                    logger.warning(f"AudioEngine: OAuth2 token generation failed: {gcp_err}. Falling back to API Key REST...")
                    api_key = self.key_manager.get_key()
                    tts_url = f"https://texttospeech.googleapis.com/v1/text:synthesize?key={api_key}"
                    tts_payload = {
                        "input": {"text": trimmed_script},
                        "voice": {"languageCode": "en-US", "name": "en-US-Journey-D"},
                        "audioConfig": {"audioEncoding": "MP3"}
                    }
                    tts_res = requests.post(tts_url, json=tts_payload)
                
                if tts_res.status_code == 429:
                    logger.warning(f"AudioEngine: TTS 429 hit (Attempt {attempt+1}). Rotating key and retrying...")
                    self.key_manager.rotate_key()
                    self._refresh_client()
                    continue

                if tts_res.status_code != 200:
                    logger.warning(f"Google Cloud TTS Failed ({tts_res.status_code}). Falling back to Google Translate TTS...")
                    if self._generate_translate_tts(script, filepath):
                        with open(filepath, 'rb') as f:
                            audio_content = f.read()
                    else:
                        logger.error("Translate TTS fallback failed. Triggering silent fallback.")
                        return self._generate_fallback_karaoke(script, filename, filepath)
                else:
                    audio_content = base64.b64decode(tts_res.json()["audioContent"])
                    with open(filepath, 'wb') as f:
                        f.write(audio_content)

                # 2. Gemini Multimodal Word Alignment (Karaoke)
                logger.info("AudioEngine: Requesting word alignment from Gemini 2.5 Flash...")
                
                audio_part = types.Part.from_bytes(data=audio_content, mime_type="audio/mp3")
                
                prompt = "You are a forensic audio transcription system. Listen to this audio and provide the transcript with word-level start and end timestamps (in seconds). Output pure JSON."
                
                response_schema = {
                    "type": "ARRAY",
                    "items": {
                        "type": "OBJECT",
                        "properties": {
                            "word": {"type": "STRING"},
                            "start": {"type": "NUMBER"},
                            "end": {"type": "NUMBER"}
                        },
                        "required": ["word", "start", "end"]
                    }
                }

                response = self.client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=[prompt, audio_part],
                    config=types.GenerateContentConfig(
                        response_mime_type='application/json',
                        response_schema=response_schema,
                        temperature=0.1
                    )
                )
                
                words = response.parsed
                if not words:
                    import re
                    text = response.text
                    text = re.sub(r'```json\s*', '', text, flags=re.IGNORECASE)
                    text = re.sub(r'```\s*', '', text).strip()
                    words = json.loads(text)
                
                return {
                    "status": "success",
                    "audio_filename": filename,
                    "words": words
                }

            except Exception as e:
                error_str = str(e)
                logger.error(f"AudioEngine Error (Attempt {attempt + 1}): {error_str}")
                
                # If Resource Exhausted or 429, Rotate Key and retry
                if any(err in error_str for err in ["Resource exhausted", "429"]) and attempt < max_retries:
                    logger.warning("AudioEngine: Quota exhausted during Gemini phase. Rotating API Key and retrying...")
                    self.key_manager.rotate_key()
                    self._refresh_client()
                    time.sleep(1)
                    continue

                if any(err in error_str for err in ["503", "UNAVAILABLE"]) and attempt < max_retries:
                    delay = base_delay * (2 ** attempt)
                    logger.warning(f"AudioEngine: Transient error. Retrying in {delay}s...")
                    time.sleep(delay)
                    continue
                
                return {"status": "error", "message": error_str}

    def _generate_fallback_karaoke(self, script: str, filename: str, filepath: str) -> Dict:
        """Generates a silent MP3 fallback with calculated linear timestamps for karaoke."""
        # 1-second silent MP3 base64
        silent_b64 = "SUQzBAAAAAAAI1RTU0UAAAAPAAADTGFtZTMuMTAwAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABMYW1lMy4xMDBVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV"
        try:
            with open(filepath, 'wb') as f:
                f.write(base64.b64decode(silent_b64))
        except Exception as e:
            logger.error(f"Error writing silent fallback MP3: {e}")
            
        words = []
        raw_words = script.split()
        current_time = 0.0
        for w in raw_words:
            clean_w = w.strip(".,!?\"()'-;:")
            if not clean_w: continue
            duration = max(0.15, min(0.6, len(clean_w) * 0.06)) # Dynamic speaking duration based on length
            words.append({
                "word": clean_w,
                "start": round(current_time, 2),
                "end": round(current_time + duration, 2)
            })
            current_time += duration + 0.04 # Gap
            
        return {
            "status": "success",
            "audio_filename": filename,
            "words": words
        }

    def _generate_translate_tts(self, script: str, filepath: str) -> bool:
        """Downloads TTS audio using Google Translate chunked API."""
        import urllib.request
        import urllib.parse
        try:
            words = script.split()
            chunks = []
            current_chunk = []
            for word in words:
                if len(" ".join(current_chunk + [word])) < 150:
                    current_chunk.append(word)
                else:
                    chunks.append(" ".join(current_chunk))
                    current_chunk = [word]
            if current_chunk:
                chunks.append(" ".join(current_chunk))

            with open(filepath, "wb") as out_file:
                for chunk in chunks:
                    if not chunk.strip(): continue
                    url = f"https://translate.google.com/translate_tts?ie=UTF-8&tl=en&client=tw-ob&q={urllib.parse.quote(chunk)}"
                    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
                    with urllib.request.urlopen(req) as response:
                        out_file.write(response.read())
            logger.info("AudioEngine: Successfully downloaded Translate TTS audio fallback.")
            return True
        except Exception as e:
            logger.error(f"AudioEngine: Translate TTS fallback failed: {e}")
            return False
