import yaml
from pathlib import Path

class Config:
    _instance = None
    
    def __init__(self):
        config_path = Path(__file__).parent.parent / 'config' / 'config.yaml'
        with open(config_path, 'r') as file:
            self.config = yaml.load(file, Loader=yaml.SafeLoader)

    def validate(self):
        if not isinstance(self.enable_cache, bool):
            raise ValueError("enable_cache must be a boolean")
    
    @classmethod
    def get_instance(cls):
        if not cls._instance:
            cls._instance = cls()
        return cls._instance

    @property
    def api_config(self):
        return self.config.get('api_config', {})
    
    @property
    def logging_config(self):
        return self.config.get('logging', {})
    
    @property
    def api_specs(self):
        return self.config.get('api_specs', {})
    
    @property
    def enable_cache(self):
        return self.config.get('enable_cache', True)