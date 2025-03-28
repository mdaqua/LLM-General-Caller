from itertools import cycle
from typing import Dict, List, Tuple
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
            raise ValueError(f"Provider {provider} not found")
        return (provider, next(self.keys_cycle[provider]))
    
    def get_random_provider(self):
        return random.choice(list(self.providers.keys()))