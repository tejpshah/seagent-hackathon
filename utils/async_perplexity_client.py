import asyncio
import aiohttp
import json
import time
import logging
import threading

logger = logging.getLogger(__name__)

class AsyncPerplexityClient:
    def __init__(self, api_key: str, api_url: str, model: str):
        self.api_key = api_key
        self.api_url = api_url
        self.model = model
        self.last_request_time = 0.0
        self.min_interval = 1.2  # 50 requests per minute (RPM)
        self.rate_lock = threading.Lock()

    async def get_response(self, session, prompt: str, response_format: dict, timeout: int = 120) -> str:
        """
        Async function to get response from Perplexity API.
        Uses aiohttp for non-blocking API calls.
        """
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
        
        # Rate limiting (ensures 1.2s between requests)
        with self.rate_lock:
            now = time.monotonic()
            elapsed = now - self.last_request_time
            if elapsed < self.min_interval:
                sleep_time = self.min_interval - elapsed
                logger.debug("Throttling request: sleeping for %.2f seconds", sleep_time)
                await asyncio.sleep(sleep_time)  # Now async
            self.last_request_time = time.monotonic()

        try:
            async with aiohttp.request("POST", self.api_url, headers=headers, json=payload, timeout=aiohttp.ClientTimeout(timeout)) as response:
                response.raise_for_status()
                json_response = await response.json()
                return json_response["choices"][0]["message"]["content"]
            
        except asyncio.TimeoutError:
            logger.error("⏳ API request timed out after %d seconds", timeout)
            return None
        except Exception as e:
            logger.error(f"❌ API request failed: {e}")
            return None