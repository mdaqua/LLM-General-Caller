import time
from collections import OrderedDict

class NullCache:
    def get(self, message):
        return None
    
    def set(self, message, response):
        pass

class MessageCache:
    def __init__(self, ttl=300, max_size=1000):
        self.ttl = ttl
        self.max_size = max_size
        self.cache = OrderedDict()
    
    def get(self, message):
        if message in self.cache:
            entry = self.cache[message]
            if (time.time() - entry['timestamp']) < self.ttl:
                self.cache.move_to_end(message)
                return entry['response']
            else:
                del self.cache[message]
        return None
    
    def set(self, message, response):
        if len(self.cache) >= self.max_size:
            self.cache.popitem(last=False)
        self.cache[message] = {
            'timestamp': time.time(),
            'response': response
        }
        # Remove oldest entries if cache exceeds size (optional)