from .base import BaseAdapter

class DifydAdapter(BaseAdapter):
    def format_request(self, message: str, **kwargs):
        base_payload = {
            "query": [{"role": "user", "content": message}],
            **self.config['required_params']
        }
        return {**base_payload, **kwargs}
    
    def parse_response(self, response: dict) -> str:
        return self.jsonpath_extract(response, self.config['content_field'])