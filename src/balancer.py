from itertools import cycle
from typing import Dict, Tuple
import random

class LoadBalancer:
    def __init__(self, providers: Dict):
        self.providers = providers
        self.keys_cycle = {}
        self._init_cycles()
    
    def _init_cycles(self):
        for provider, config in self.providers.items():
            keys = config['keys']
            random.shuffle(keys)
            self.keys_cycle[provider] = cycle(keys)
    
    def get_next_key(self, provider: str) -> Tuple[str, str]:
        """返回 (provider_name, api_key)"""
        if provider not in self.providers:
            raise ValueError(f"Provider {provider} not configured")
        return (provider, next(self.keys_cycle[provider]))
    
    def get_specific_key(self, provider: str, key_index: int = 0) -> Tuple[str, str]:
        """获取指定供应商的特定索引的Key"""
        if provider not in self.providers:
            raise ValueError(f"Provider {provider} not configured")
        
        keys = self.providers[provider]['keys']
        if key_index >= len(keys):
            raise IndexError(f"Provider {provider} only has {len(keys)} keys available")
            
        return (provider, keys[key_index])
    
    def get_random_provider(self):
        return random.choice(list(self.providers.keys()))