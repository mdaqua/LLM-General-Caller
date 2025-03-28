import time
import requests
import logging
from typing import Optional, Tuple
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
    
    def send_request(self, message, provider: Optional[str] = None, **kwargs):
        cached_response = self.cache.get(message)
        if cached_response:
            return cached_response
        
        if not provider:
            provider = self.balancer.get_random_provider()
        provider, api_key = self.balancer.get_next_key(provider)
        
        adapter = self._get_adapter(provider)
        endpoint = self.config.api_specs[provider]['endpoint']
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            # 构建供应商特定的请求
            payload = adapter.format_request(message, **kwargs)
            start_time = time.time()
            
            response = requests.post(
                self.balancer.providers[provider]['base_url'] + endpoint,
                headers=headers,
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            response_data = response.json()
            
            # 标准化响应
            parsed_content = adapter.parse_response(response_data)
            standard_response = {
                "provider": provider,
                "content": parsed_content,
                "raw": response_data
            }
            
            self.monitor.record_request(True, time.time()-start_time)
            self.cache.set(message, standard_response)
            return standard_response
            
        except Exception as e:
            logger.error(f"API request failed: {str(e)}")
            self.monitor.record_request(False, time.time()-start_time)
            raise
