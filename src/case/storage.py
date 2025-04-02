import json
from pathlib import Path
from typing import Dict, Union
from .graph_mapper import CaseGraphMapper
from src.db.neo4j_client import Neo4jClient
from src.case.models import CaseData

class CaseStorage:
    def __init__(self, storage_path: str = "./case_data", neo4j_config: Dict = None):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # 图数据库客户端
        self.neo4j_client = Neo4jClient(neo4j_config) if neo4j_config else None

    def save_case(self, case_data: Union[CaseData, Dict]) -> str:
        """保存案件数据到文件和图数据库"""
        if isinstance(case_data, dict):
            case_data = CaseData(**case_data)
            
        # JSON存储
        json_path = self._save_to_json(case_data)
        
        # 图数据库存储
        if self.neo4j_client:
            self._save_to_neo4j(case_data)
            
        return json_path

    def _save_to_json(self, case_data: CaseData) -> str:
        filepath = self._generate_filename(case_data.id)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(case_data.dict(), f, ensure_ascii=False, indent=2)
        return str(filepath)

    def _save_to_neo4j(self, case_data: CaseData):
        try:
            queries = CaseGraphMapper.case_to_cypher(case_data)
            with self.neo4j_client.driver.session() as session:
                for query in queries:
                    session.run(query["query"], parameters=query["params"])
        except Exception as e:
            self.logger.error(f"Neo4j存储失败: {str(e)}")
            raise