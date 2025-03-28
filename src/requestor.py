import concurrent.futures
from typing import List, Dict
import threading

class RequestCoordinator:
    def __init__(self, client, max_workers=5):
        self.client = client
        self.max_workers = max_workers
        self.lock = threading.Lock()
        self.completed = 0
        self.results = []
    
    def process_request(self, message, provider=None):
        try:
            result = self.client.send_request(message, provider)
            with self.lock:
                self.completed += 1
                self.results.append(result)
            return result
        except Exception as e:
            # Handle error
            return {"error": str(e)}
    
    def batch_request(self, messages: List[str], provider=None):
        self.completed = 0
        self.results = []
        total = len(messages)
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(self.process_request, msg, provider): msg 
                for msg in messages
            }
            
            for future in concurrent.futures.as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    logger.error(f"Request failed: {str(e)}")
                
                print(f"Progress: {self.completed}/{total} completed")
        
        return self.results