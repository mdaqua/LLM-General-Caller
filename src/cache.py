import time
from collections import OrderedDict

class MessageCache:
    def __init__(self, ttl):
        self.ttl = ttl
        self.cache = OrderedDict()
    
    def get(self, message):
        entry = self.cache.get(message)
        if entry and (time.time() - entry['timestamp']) < self.ttl:
            return entry['response']
        return None
    
    def set(self, message, response):
        self.cache[message] = {
            'timestamp': time.time(),
            'response': response
        }
        # Remove oldest entries if cache exceeds size (optional)