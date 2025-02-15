import requests
import logging

logger = logging.getLogger(__name__)

class PerplexityClient:
    def __init__(self, api_key: str, api_url: str, model: str):
        self.api_key = api_key
        self.api_url = api_url
        self.model = model

    def get_response(self, prompt: str, response_format: dict, timeout: int = 30) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "Be precise and concise."},
                {"role": "user", "content": prompt}
            ],
            "response_format": response_format
        }
        try:
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=timeout)
            response.raise_for_status()
            json_response = response.json()
            content = json_response["choices"][0]["message"]["content"]
            return content
        except Exception as e:
            logger.error("Error calling Perplexity API: %s", e, exc_info=True)
            raise
