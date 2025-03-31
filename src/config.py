import os
import yaml

class Config:
    _instance = None
    
    def __init__(self):
        with open(os.path.join(os.path.dirname(__file__), '../config/config.yaml')) as f:
            self.config = yaml.safe_load(f)
    
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