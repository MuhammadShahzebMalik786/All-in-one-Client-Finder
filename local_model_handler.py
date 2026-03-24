"""
Local Model Handler — CPU-based fallback using Ollama
Supports tiny models (~2GB):
  - phi (2.7GB) — fastest, lightweight
  - neural-chat (4GB) — good balance
  - mistral (4GB) — more capable
"""

import os
import sys
import subprocess
import requests
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import Config


class LocalModelHandler:
    """Manages local LLM using Ollama."""

    def __init__(self, model: str = "mistral"):
        """
        Initialize local model handler.
        Args:
            model: Ollama model name (mistral, neural-chat, phi, etc.)
        """
        self.config = Config()
        self.model = model
        self.base_url = "http://localhost:11434/api"
        self.timeout = 300  # 5 min timeout for generation
        self.available = False

        # Check if Ollama is running
        self._check_ollama()

    def _check_ollama(self) -> bool:
        """Check if Ollama service is running."""
        try:
            resp = requests.get(f"{self.base_url}/tags", timeout=5)
            if resp.status_code == 200:
                self.available = True
                print(f"[+] Ollama running locally on 11434")
                return True
        except requests.exceptions.RequestException:
            pass

        print("[!] Ollama not running. To enable local fallback:")
        print("    Download: https://ollama.ai")
        print(f"    Then run: ollama pull {self.model}")
        print("    Then run: ollama serve")
        return False

    def ensure_model(self) -> bool:
        """Download/pull model if not available."""
        if not self.available:
            return False

        try:
            resp = requests.get(f"{self.base_url}/tags", timeout=5)
            models = resp.json().get("models", [])
            model_names = [m.get("name", "") for m in models]

            if not any(self.model in name for name in model_names):
                print(f"[*] Pulling {self.model}... (first time, ~2-5 min)")
                subprocess.run(
                    ["ollama", "pull", self.model],
                    capture_output=True,
                    timeout=600,
                )
            return True
        except Exception as e:
            print(f"[!] Model check failed: {e}")
            return False

    def generate(self, prompt: str, system: Optional[str] = None) -> Optional[str]:
        """
        Generate text using local model.
        Args:
            prompt: User prompt
            system: Optional system prompt
        Returns:
            Generated text or None if failed
        """
        if not self.available:
            return None

        try:
            data = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "num_ctx": 2048,
                },
            }

            if system:
                data["system"] = system

            resp = requests.post(
                f"{self.base_url}/generate",
                json=data,
                timeout=self.timeout,
            )

            if resp.status_code == 200:
                result = resp.json()
                return result.get("response", "").strip()
            else:
                print(f"[!] Ollama error: {resp.status_code}")
                return None

        except requests.exceptions.Timeout:
            print("[!] Local model generation timeout (no GPU?)")
            return None
        except Exception as e:
            print(f"[!] Local model error: {e}")
            return None

    def is_available(self) -> bool:
        """Check if local model is ready to use."""
        return self.available


def get_local_model_fallback(model: str = "phi") -> LocalModelHandler:
    """Factory function for local model."""
    return LocalModelHandler(model)


if __name__ == "__main__":
    # Test local model
    handler = get_local_model_fallback()

    if handler.is_available():
        print("\n[*] Testing local model...\n")

        prompt = "Write a 2-sentence cold pitch for someone selling automation services."
        result = handler.generate(prompt)

        if result:
            print(f"Local Model Output:\n{result}\n")
        else:
            print("[!] Model generation failed")
    else:
        print("\n[!] Local model not available. Install Ollama first.")
