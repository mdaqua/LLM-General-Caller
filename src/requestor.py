import time
import threading
import concurrent.futures
from typing import List, Optional, Dict, Callable
import logging

logger = logging.getLogger(__name__)

class RequestCoordinator:
    def __init__(self, client, max_workers=5):
        self.client = client
        self.max_workers = max_workers
        self.lock = threading.Lock()
        self.progress = {'total': 0, 'completed': 0, 'success': 0, 'failed': 0}
        self.results = []
        self.errors = []
        self.rate_limit = {}
        self.locks = {}

        for provider, provider_config in self.client.balancer.providers.items():
            rpm = provider_config.get('rpm', 60)
            self.rate_limit[provider] = {
                "rpm": rpm,
                "min_interval": 60 / rpm,
                "last_request_time": 0
            }
            self.locks[provider] = threading.Lock()

    def _apply_rate_limit(self, provider: str):
        """
        Apply rate limiting for the given provider.
        """
        rate_limit = self.rate_limit[provider]
        min_interval = rate_limit["min_interval"]

        with self.locks[provider]:
            current_time = time.time()
            elapsed_time = current_time - rate_limit["last_request_time"]
            if elapsed_time < min_interval:
                time.sleep(min_interval - elapsed_time)
            rate_limit["last_request_time"] = time.time()
            
    def batch_request(
        self,
        messages: List[str],
        provider: Optional[str] = None,
        api_key: Optional[str] = None,
        key_index: Optional[int] = None,
        callback: Optional[Callable[[Dict], None]] = None,
        **kwargs
    ) -> List[Dict]:
        self.progress = {'total': len(messages), 'completed': 0, 'success': 0, 'failed': 0}
        self.results = []
        self.errors = []

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(
                    self._process_request,
                    message,
                    provider,
                    api_key,
                    key_index,
                    **kwargs
                ): message for message in messages
            }
            
            for future in concurrent.futures.as_completed(futures):
                try:
                    result = future.result()
                    self.results.append(result)
                    if result["success"]:
                        self._update_progress(success=True)
                    else:
                        self._update_progress(success=False)
                        self.errors.append(result)
                    if callback:
                        callback(result)
                except Exception as e:
                    error_message = f"Request failed: {futures[future]} - {str(e)}"
                    logger.error(error_message)
                    self.errors.append({"message": futures[future], "error": str(e)})
                    self._update_progress(success=False)
                        
        return self.results
    
    def _process_request(self, message, provider, api_key, key_index, **kwargs):
        try:
            if self.client.cache is not None:
                if cached := self.client.cache.get(message):
                    return cached
                
            if api_key:
                provider = self.client._detect_provider(api_key)
                selected_key = api_key
            elif provider:
                if key_index is not None:
                    provider, selected_key = self.client.balancer.get_specific_key(provider, key_index)
                else:
                    provider, selected_key = self.client.balancer.get_next_key(provider)
            else:
                provider = self.client.balancer.get_random_provider()
                provider, selected_key = self.client.balancer.get_next_key(provider)

            self._apply_rate_limit(provider)

            result = self.client.send_request(
                message,
                provider=provider,
                api_key=selected_key,
                key_index=key_index,
                **kwargs
            )
            return result
        except Exception as e:
            logger.error(f"Error processing request: {message} - {str(e)}")
            return {"success": False, "error": str(e), "message": message}
    
    def _update_progress(self, success: bool):
        with self.lock:
            self.progress['completed'] += 1
            if success:
                self.progress['success'] += 1
            else:
                self.progress['failed'] += 1
            logger.info(
                f"Progress: {self.progress['completed']}/{self.progress['total']} "
                f"(Success: {self.progress['success']}, Failed: {self.progress['failed']})"
            )

    def get_progress(self):
        return self.progress.copy()
    
    def get_errors(self):
        return self.errors.copy()