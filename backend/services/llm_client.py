"""
LLM Client Service: Gemini API Integration.
Isolated provider client for Gemini API so that switching LLM providers
(e.g., Anthropic, OpenAI, local Ollama) only requires modifying this single file.
"""
import os
import json
import logging
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("llm_client")

class LLMClient:
    """Encapsulates interaction with the Google Gemini API."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "").strip()
        self.provider = "gemini"
        self._init_client()

    def _init_client(self):
        """Initializes the Gemini SDK client."""
        if not self.api_key:
            logger.warning("No GEMINI_API_KEY detected in environment.")
            self._client = None
            return

        # Attempt modern google-genai SDK first
        try:
            from google import genai
            self._client = genai.Client(api_key=self.api_key)
            self._sdk_type = "genai"
            logger.info("Initialized Google GenAI SDK client.")
            return
        except Exception as e:
            logger.info(f"GenAI SDK initialization note: {e}. Falling back to google.generativeai.")

        # Fallback to google.generativeai SDK if available
        try:
            import google.generativeai as legacy_genai
            legacy_genai.configure(api_key=self.api_key)
            self._client = legacy_genai.GenerativeModel("gemini-1.5-flash")
            self._sdk_type = "generativeai"
            logger.info("Initialized legacy google.generativeai SDK client.")
        except Exception as err:
            logger.error(f"Failed to initialize any Gemini SDK: {err}")
            self._client = None
            self._sdk_type = None

    def is_configured(self) -> bool:
        """Returns True if an API key is available and configured."""
        return bool(self.api_key and self._client)

    def generate_text(self, prompt: str, system_instruction: Optional[str] = None) -> str:
        """
        Sends prompt to Gemini model and returns raw text response.
        Raises RuntimeError with helpful messaging if key is missing or call fails.
        """
        if not self.api_key:
            raise ValueError(
                "Gemini API key is not configured. Please set GEMINI_API_KEY in backend/.env"
            )

        if not self._client:
            self._init_client()
            if not self._client:
                raise RuntimeError("Failed to initialize Gemini API client. Please verify your GEMINI_API_KEY.")

        try:
            if self._sdk_type == "genai":
                config = {}
                if system_instruction:
                    config["system_instruction"] = system_instruction
                
                # Using gemini-2.5-flash or gemini-1.5-flash
                response = self._client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt,
                    config=config if config else None,
                )
                return response.text or ""

            elif self._sdk_type == "generativeai":
                full_prompt = f"System: {system_instruction}\n\nUser: {prompt}" if system_instruction else prompt
                response = self._client.generate_content(full_prompt)
                return response.text or ""

            else:
                raise RuntimeError("No compatible Gemini SDK available.")

        except Exception as exc:
            err_str = str(exc)
            if "API_KEY_INVALID" in err_str or "invalid" in err_str.lower() and "key" in err_str.lower():
                raise ValueError("Invalid Gemini API Key. Please check the key in backend/.env") from exc
            if "RESOURCE_EXHAUSTED" in err_str or "429" in err_str:
                raise RuntimeError("Gemini API rate limit exceeded. Please wait a moment and try again.") from exc
            raise RuntimeError(f"Gemini API invocation error: {err_str}") from exc


# Global singleton instance for easy dependency injection
llm_client = LLMClient()
