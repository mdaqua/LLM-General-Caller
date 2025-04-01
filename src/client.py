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
                     provider: Optional[str] = None,
                     api_key: Optional[str] = None,
                     key_index: Optional[int] = None,
                     **kwargs):
        if self.cache is not None:
            if cached := self.cache.get(message):
                return cached
        
        if api_key:
            provider = self._detect_provider(api_key)
            selected_key = api_key
        elif provider:
            if key_index is not None:
                provider, selected_key = self.balancer.get_specific_key(provider, key_index)
            else:
                provider, selected_key = self.balancer.get_next_key(provider)
        else:
            provider = self.config.api_config['default_provider']
            provider, selected_key = self.balancer.get_next_key(provider)
        
        adapter = self._get_adapter(provider)
        endpoint = self.config.api_specs[provider].get('endpoint', '')
        
        url = f"{self.balancer.providers[provider]['base_url']}{endpoint}"
        headers = {
            "Authorization": f"Bearer {selected_key}",
            "Content-Type": "application/json"
        }
        
        try:
            # 构建供应商特定的请求
            payload = adapter.format_request(message, **kwargs)
            start_time = time.time()
            
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=10
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
            logger.error(f"API request failed: {str(e)}")
            self.monitor.record_request(provider, False, time.time()-start_time)
            return {
                "provider": provider,
                "error": str(e),
                "success": False,
            }