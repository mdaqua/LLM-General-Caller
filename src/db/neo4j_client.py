from neo4j import GraphDatabase, BoltDriver
from neo4j.exceptions import Neo4jError
from typing import Optional, Dict, Any, List
from pathlib import Path
import logging

class Neo4jClient:
    def __init__(self, config: Dict):
        self.driver = GraphDatabase.driver(
            config['uri'],
            auth=(config['username'], config['password']),
            encrypted=config['encrypted'],
            max_connection_pool_size=config['max_connection_pool_size']
        )
        self.logger = logging.getLogger(__name__)
        self._verify_connection()

    def _verify_connection(self):
        try:
            with self.driver.session() as session:
                session.run("RETURN 1")
            self.logger.info("Neo4j connection verified")
        except Neo4jError as e:
            self.logger.error(f"Neo4j connection failed: {e}")
            raise

    def execute_query(self, query: str, params: Optional[Dict] = None) -> List[Dict[str, Any]]:
        try:
            with self.driver.session() as session:
                result = session.run(query, parameters=params)
                return [dict(record) for record in result]
        except Neo4jError as e:
            self.logger.error(f"Neo4j query failed: {e.code} - {e.message}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error: {str(e)}")
            raise

    def close(self):
        self.driver.close()