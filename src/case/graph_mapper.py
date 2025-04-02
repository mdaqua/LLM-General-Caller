from .models import CaseData
from typing import Dict, List

class CaseGraphMapper:
    @staticmethod
    def case_to_cypher(case: CaseData) -> List[Dict]:
        """将案件数据转换为Cypher查询和参数"""
        base_node = {
            "id": case.id,
            "title": case.title,
            "keywords": case.keywords,
            "resolution": case.resolution,
            "is_major": case.degree.is_major,
            "is_sensitive": case.degree.is_sensitive
        }

        queries = []
        # 创建案件主节点
        queries.append({
            "query": """
            CREATE (c:Case $props)
            SET c.created_at = datetime()
            """,
            "params": {"props": base_node}
        })

        # 添加时间关系
        time_props = case.time.dict()
        queries.append({
            "query": """
            MATCH (c:Case {id: $case_id})
            CREATE (c)-[:HAS_TIMELINE]->(t:TimeLine)
            SET t += $props
            """,
            "params": {"case_id": case.id, "props": time_props}
        })

        # 添加地理位置节点
        location_props = case.location.dict()
        queries.append({
            "query": """
            MATCH (c:Case {id: $case_id})
            MERGE (loc:Location {detail: $detail})
            ON CREATE SET loc += $props
            CREATE (c)-[:OCCURRED_AT]->(loc)
            """,
            "params": {"case_id": case.id, "props": location_props, "detail": case.location.detail}
        })

        # 处理人物关系
        for idx, subject in enumerate(case.details.subject):
            queries.extend(CaseGraphMapper._create_person_relations(
                case.id, subject, "SUBJECT", idx+1
            ))

        for idx, obj in enumerate(case.details.object):
            queries.extend(CaseGraphMapper._create_person_relations(
                case.id, obj, "OBJECT", idx+1
            ))

        # 添加机构关系
        for org in case.elements.organizations:
            queries.append({
                "query": """
                MATCH (c:Case {id: $case_id})
                MERGE (o:Organization {name: $org_name})
                CREATE (c)-[:INVOLVES_ORGANIZATION]->(o)
                """,
                "params": {"case_id": case.id, "org_name": org}
            })

        return queries

    @staticmethod
    def _create_person_relations(case_id: str, person: dict, role: str, order: int):
        queries = []
        person_props = person.dict()
        
        # 创建人员节点
        queries.append({
            "query": f"""
            MATCH (c:Case {{id: $case_id}})
            MERGE (p:Person {{id_card: $id_card}})
            ON CREATE SET p += $props
            CREATE (c)-[r:HAS_{role} {{
                order: $order
            }}]->(p)
            """,
            "params": {
                "case_id": case_id,
                "id_card": person.id_card,
                "props": person_props,
                "order": order
            }
        })

        # 创建电话号码关系
        queries.append({
            "query": """
            MATCH (p:Person {id_card: $id_card})
            MERGE (n:PhoneNumber {number: $phone})
            CREATE (p)-[:HAS_PHONE]->(n)
            """,
            "params": {"id_card": person.id_card, "phone": person.phone}
        })

        return queries