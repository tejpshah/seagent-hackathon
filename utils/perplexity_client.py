import requests
import logging
import json
import time
import threading

logger = logging.getLogger(__name__)
class PerplexityClient:
    def __init__(self, api_key: str, api_url: str, model: str):
        self.api_key = api_key
        self.api_url = api_url
        self.model = model
        self.last_request_time = 0.0
        self.min_interval = 1.2  # seconds between requests (50 RPM)
        self.rate_lock = threading.Lock()

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
        
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("Request payload: %s", json.dumps(payload, indent=2))
        
        # Rate limiting: ensure at least min_interval seconds between requests
        with self.rate_lock:
            now = time.monotonic()
            elapsed = now - self.last_request_time
            if elapsed < self.min_interval:
                sleep_time = self.min_interval - elapsed
                logger.debug("Throttling request: sleeping for %.2f seconds", sleep_time)
                time.sleep(sleep_time)
            self.last_request_time = time.monotonic()
        
        try:
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=timeout)
            response.raise_for_status()
            json_response = response.json()
            
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug("Response payload: %s", json.dumps(json_response, indent=2))
                
            content = json_response["choices"][0]["message"]["content"]
            return content
        except Exception as e:
            logger.error("Error calling Perplexity API: %s", e, exc_info=True)
            raise
