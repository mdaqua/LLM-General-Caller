import time
import requests
import logging
from typing import Optional
from .adapters import get_adapter
from .case.models import CaseData

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
    
    def process_case_description(self, description: str, **kwargs) -> CaseData:
        response = self.send_request(description, **kwargs)
        
        try:
            # 原始响应处理
            raw_data = response['content']
            
            # 预处理特殊值
            def preprocess(data):
                if isinstance(data, dict):
                    return {k: preprocess(v) for k, v in data.items()}
                if isinstance(data, list):
                    return [preprocess(item) for item in data]
                if data in ["无", "不详", "未知", "暂无"]:
                    return "暂无"
                return data

            processed_data = preprocess(raw_data)
            
            # 解析为数据模型
            return CaseData(**processed_data)
        except Exception as e:
            error_msg = f"数据解析失败: {str(e)}\n原始数据：{raw_data}"
            raise ValueError(error_msg)