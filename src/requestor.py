import concurrent.futures
from typing import List, Optional, Dict
import threading
import logger

class RequestCoordinator:
    def __init__(self, client, max_workers=5):
        self.client = client
        self.max_workers = max_workers
        self.lock = threading.Lock()
        self.progress = {'total': 0, 'completed': 0, 'success': 0}
        self.results = []
            
    def batch_request(
        self,
        messages: List[str],
        provider: Optional[str] = None,
        api_key: Optional[str] = None,
        key_index: Optional[int] = None,
        **kwargs
    ) -> List[Dict]:
        self.progress = {'total': len(messages), 'completed': 0, 'success': 0}
        self.results = []

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
                except Exception as e:
                    logger.error(f"Request failed: {str(e)}")
                        
        return self.results
    
    def _process_request(self, message, provider, api_key, key_index, **kwargs):
        result = self.client.send_request(
            message,
            provider=provider,
            api_key=api_key,
            key_index=key_index,
            **kwargs
        )
        with self.lock:
            self.progress['completed'] += 1
            if result["success"]:
                self.progress['success'] += 1
        return result

    def get_progress(self):
        return self.progress.copy()