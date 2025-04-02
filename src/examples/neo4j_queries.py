from src.db.neo4j_client import Neo4jClient
from src.case.models import CaseData

def get_case_relations(case_id: str, neo4j_client: Neo4jClient):
    """查询案件关联关系"""
    query = """
    MATCH (c:Case {id: $case_id})-[r*..3]-(related)
    RETURN c, r, related
    """
    return neo4j_client.execute_query(query, {"case_id": case_id})

def find_similar_cases(case_data: CaseData, neo4j_client: Neo4jClient):
    """查找相似案件"""
    query = """
    MATCH (c:Case)-[:HAS_SUBJECT]->(p:Person)
    WHERE p.id_card IN $id_cards
    RETURN c.id as caseId, count(p) AS commonPersons
    ORDER BY commonPersons DESC
    LIMIT 5
    """
    id_cards = [s.id_card for s in case_data.details.subject]
    return neo4j_client.execute_query(query, {"id_cards": id_cards})