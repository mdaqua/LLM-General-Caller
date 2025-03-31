import json
from pathlib import Path
from datetime import datetime
from typing import Union, Dict
from .models import CaseData
import threading

class CaseStorage:
    _lock = threading.Lock()

    def __init__(self, storage_path: str = "./case_data"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
    
    def _generate_filename(self, case_id: str) -> Path:
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return self.storage_path / f"case_{case_id}_{timestamp}.json"
    
    def save_case(self, case_data: Union[CaseData, Dict]) -> str:
        if isinstance(case_data, dict):
            case_data = CaseData(**case_data)
            
        filepath = self._generate_filename(case_data.id)
        
        with self._lock:  # 添加线程锁
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(case_data.dict(), f, ensure_ascii=False, indent=2)
            except Exception as e:
                raise IOError(f"文件存储失败: {str(e)}")
        
        return str(filepath)
    
    def load_case(self, filepath: str) -> CaseData:
        """从文件加载案件数据"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return CaseData(**data)
    
    def validate_json(self, json_data: Dict) -> bool:
        """验证JSON数据是否符合规范"""
        try:
            CaseData(**json_data)
            return True
        except Exception:
            return False