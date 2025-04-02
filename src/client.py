import time
import requests
import logging
from typing import Optional
from .adapters import get_adapter

logger = logging.getLogger(__name__)

class APIClient:
    def __init__(self, cache, monitor, balancer, config):
        self.cache = cache
        self.monitor = monitor
        self.balancer = balancer
        self.config = config
        self.adapters = {}
        
    def _get_adapter(self, provider: str):
        if provider not in self.adapters:
            spec = self.config.api_specs.get(provider, {})
            self.adapters[provider] = get_adapter(provider, spec)
        return self.adapters[provider]
    
    def _detect_provider(self, api_key: str) -> str:
        for provider, config in self.balancer.providers.items():
            if any(key.startswith(api_key[:3]) for key in config['keys']):
                return provider
        raise ValueError("Cannot determine provider from API key")
    
    def send_request(self,
                     message: str,
                     provider: str,
                     api_key: str,
                     **kwargs):        
        adapter = self._get_adapter(provider)
        endpoint = self.config.api_specs[provider].get('endpoint', '')
        timeout = self.config.api_config.get('timeout', 30)
        max_retries = self.config.api_config.get('max_retries', 3)
        retry_delay = self.config.api_config.get('retry_delay', 1)
        
        url = f"{self.balancer.providers[provider]['base_url']}{endpoint}"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        for attempt in range(max_retries):
            try:
                # 构建供应商特定的请求
                payload = adapter.format_request(message, **kwargs)
                start_time = time.time()
                
                response = requests.post(
                    url,
                    headers=headers,
                    json=payload,
                    timeout=timeout
                )
                response.raise_for_status()
                response_data = response.json()
                
                # 标准化响应
                content = adapter.parse_response(response_data)
                result = {
                    "provider": provider,
                    "content": content,
                    "raw": response_data,
                    "success": True,
                }
                
                self.monitor.record_request(provider, True, time.time()-start_time)
                if self.cache is not None:
                    self.cache.set(message, result)
                return result
                
            except Exception as e:
                logger.error(f"Attempt {attempt + 1}/{max_retries} failed: {str(e)}")
                if attempt == max_retries - 1:
                    self.monitor.record_request(provider, False, time.time()-start_time)
                    return {
                        "provider": provider,
                        "error": str(e),
                        "success": False,
                    }
                time.sleep(retry_delay)