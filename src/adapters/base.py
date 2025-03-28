from abc import ABC, abstractmethod
import jsonpath_rw

class BaseAdapter(ABC):
    def __init__(self, config):
        self.config = config
    
    @abstractmethod
    def format_request(self, message: str, **kwargs) -> dict:
        """将通用消息格式转换为供应商特定格式"""
        pass
    
    @abstractmethod
    def parse_response(self, response: dict) -> str:
        """从供应商响应中提取标准化的内容"""
        pass
    
    @staticmethod
    def jsonpath_extract(data, path):
        expr = jsonpath_rw.parse(path)
        matches = [match.value for match in expr.find(data)]
        return matches[0] if matches else None