import os

import requests

from api.config import Config


class GroqClient:
    def __init__(self, api_key: str = None, api_url: str = None):
        self.api_key = api_key or Config.GROQ_API_KEY
        self.api_url = api_url or Config.GROQ_API_URL

        if not self.api_key:
            raise RuntimeError("GROQ_API_KEY not configured")

        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def chat_completion(
        self,
        system_prompt: str,
        user_prompt: str,
        model: str = "llama-3.3-70b-versatile",
        max_tokens: int = 3000,
        timeout: int = 30,
    ):
        try:
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "max_tokens": max_tokens,
                "temperature": 1,
            }
            resp = requests.post(
                self.api_url, headers=self.headers, json=payload, timeout=timeout
            )
            if resp.status_code != 200:
                raise RuntimeError(f"Groq API error: {resp.status_code} - {resp.text}")
            data = resp.json()
            # try to be robust with response shapes
            choices = data.get("choices")
            if choices and isinstance(choices, list) and choices:
                # chat-style
                content = (
                    choices[0].get("message", {}).get("content")
                    or choices[0].get("text")
                    or ""
                )
                return content
            # fallback
            return data.get("text", "")

        except Exception as e:
            print("There was an error calling groq api:", e)
