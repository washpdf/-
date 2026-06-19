# backend/knowledge_graph.py

from neo4j import GraphDatabase
import json
from neo4j_config import NEO4J_CONFIG, KG_CONFIG, ERROR_CONFIG

class KnowledgeGraph:
    """蒙医知识图谱管理"""
    
    def __init__(self, uri, user, password):
        """初始化Neo4j连接"""
        self.uri = uri
        self.user = user
        self.password = password
        self.driver = None
        self.connected = False
        self._connect()
    
    def _connect(self):
        """建立数据库连接"""
        try:
            self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
            with self.driver.session() as session:
                session.run("RETURN 1")
            self.connected = True
            print("Neo4j数据库连接成功")
        except Exception as e:
            print(f"Neo4j数据库连接失败: {e}")
            self.connected = False
    
    def close(self):
        """关闭连接"""
        if self.driver:
            try:
                self.driver.close()
            except Exception as e:
                print(f"关闭连接时出错: {e}")
    
    def create_three_roots_model(self):
        """创建三根本体模型"""
        if not self.connected:
            print("数据库未连接，跳过知识图谱初始化")
            return False
        
        try:
            with self.driver.session() as session:
                session.execute_write(self._create_three_roots)
                session.execute_write(self._create_symptoms)
                session.execute_write(self._create_pulse_features)
                session.execute_write(self._create_treatment_methods)
            print("知识图谱模型创建成功")
            return True
        except Exception as e:
            print(f"创建知识图谱模型失败: {e}")
            return False
    
    def _create_three_roots(self, tx):
        """创建三根节点"""
        roots = [
            {"name": "赫依", "description": "气，主导精神活动和生命机能", "state": "平衡"},
            {"name": "希拉", "description": "火，主导消化和代谢功能", "state": "平衡"},
            {"name": "巴达干", "description": "水和土，主导营养和生长功能", "state": "平衡"}
        ]
        
        for root in roots:
            tx.run("""
                MERGE (r:Root {name: $name})
                SET r.description = $description, r.state = $state
            """, **root)
    
    def _create_symptoms(self, tx):
        """创建症状节点和关系"""
        symptoms_data = {
            "赫依": [
                {"name": "心慌", "description": "心跳加快，心悸不安"},
                {"name": "失眠", "description": "难以入睡或睡眠质量差"},
                {"name": "手脚麻木", "description": "手脚感觉异常，麻木不仁"},
                {"name": "头晕", "description": "头部眩晕，站立不稳"},
                {"name": "胸闷", "description": "胸部憋闷，呼吸不畅"}
            ],
            "希拉": [
                {"name": "口干", "description": "口腔干燥，口渴多饮"},
                {"name": "口苦", "description": "口中有苦味"},
                {"name": "心烦", "description": "心情烦躁，易怒"},
                {"name": "目赤", "description": "眼睛发红，充血"},
                {"name": "喜冷饮", "description": "喜欢喝冷的饮料"}
            ],
            "巴达干": [
                {"name": "怕冷", "description": "容易感到寒冷"},
                {"name": "腹胀", "description": "腹部胀满不适"},
                {"name": "腹泻", "description": "大便稀溏，次数增多"},
                {"name": "痰多清稀", "description": "痰液稀薄，量多"},
                {"name": "口淡", "description": "口中无味，食欲减退"}
            ]
        }
        
        for root_name, symptoms in symptoms_data.items():
            for symptom in symptoms:
                tx.run("""
                    MERGE (s:Symptom {name: $symptom_name})
                    SET s.description = $symptom_description
                    MERGE (r:Root {name: $root_name})
                    MERGE (s)-[:RELATED_TO]->(r)
                """, 
                symptom_name=symptom["name"],
                symptom_description=symptom["description"],
                root_name=root_name
            )
    
    def _create_pulse_features(self, tx):
        """创建脉象特征节点和关系"""
        pulse_data = {
            "赫依": {
                "length": "偏短",
                "width": "偏细",
                "rhythm": "不匀"
            },
            "希拉": {
                "length": "偏长",
                "width": "偏宽",
                "rhythm": "快速匀整"
            },
            "巴达干": {
                "length": "偏短",
                "width": "偏宽",
                "rhythm": "缓慢匀整"
            }
        }
        
        for root_name, pulse_features in pulse_data.items():
            for feature_type, feature_value in pulse_features.items():
                tx.run("""
                    MERGE (p:PulseFeature {type: $feature_type, value: $feature_value})
                    MERGE (r:Root {name: $root_name})
                    MERGE (r)-[:HAS_PULSE_FEATURE]->(p)
                """,
                feature_type=feature_type,
                feature_value=feature_value,
                root_name=root_name
            )
    
    def _create_treatment_methods(self, tx):
        """创建调理方法节点和关系"""
        treatment_data = {
            "赫依": [
                {"name": "饮食调理", "description": "食用温热、易消化的食物"},
                {"name": "起居调理", "description": "保持规律作息，避免过度劳累"},
                {"name": "情志调理", "description": "保持心情平和，避免情绪波动"}
            ],
            "希拉": [
                {"name": "饮食调理", "description": "食用清凉、清淡的食物"},
                {"name": "起居调理", "description": "避免高温环境，保持室内凉爽"},
                {"name": "情志调理", "description": "保持心情舒畅，避免急躁易怒"}
            ],
            "巴达干": [
                {"name": "饮食调理", "description": "食用温热、辛辣的食物"},
                {"name": "起居调理", "description": "保持温暖，避免寒冷环境"},
                {"name": "情志调理", "description": "保持积极乐观的心态"}
            ]
        }
        
        for root_name, treatments in treatment_data.items():
            for treatment in treatments:
                tx.run("""
                    MERGE (t:Treatment {name: $treatment_name})
                    SET t.description = $treatment_description
                    MERGE (r:Root {name: $root_name})
                    MERGE (r)-[:HAS_TREATMENT]->(t)
                """,
                treatment_name=treatment["name"],
                treatment_description=treatment["description"],
                root_name=root_name
            )
    
    def get_root_by_symptoms(self, symptoms):
        """根据症状查询对应的根"""
        if not self.connected:
            return self._get_default_root_match(symptoms)
        
        try:
            with self.driver.session() as session:
                result = session.execute_read(self._match_root_by_symptoms, symptoms)
                return result
        except Exception as e:
            print(f"查询症状匹配失败: {e}")
            return self._get_default_root_match(symptoms)
    
    def _match_root_by_symptoms(self, tx, symptoms):
        """根据症状匹配根"""
        query = """
            MATCH (s:Symptom)-[:RELATED_TO]->(r:Root)
            WHERE s.name IN $symptoms
            RETURN r.name as root, count(s) as score
            ORDER BY score DESC
        """
        result = tx.run(query, symptoms=symptoms)
        return [dict(record) for record in result]
    
    def _get_default_root_match(self, symptoms):
        """获取默认的根匹配结果"""
        root_scores = {"赫依": 0, "希拉": 0, "巴达干": 0}
        
        heyi_symptoms = ["心慌", "失眠", "手脚麻木", "头晕", "胸闷"]
        xila_symptoms = ["口干", "口苦", "心烦", "目赤", "喜冷饮"]
        badagan_symptoms = ["怕冷", "腹胀", "腹泻", "痰多清稀", "口淡"]
        
        for symptom in symptoms:
            if symptom in heyi_symptoms:
                root_scores["赫依"] += 1
            elif symptom in xila_symptoms:
                root_scores["希拉"] += 1
            elif symptom in badagan_symptoms:
                root_scores["巴达干"] += 1
        
        result = []
        for root, score in root_scores.items():
            if score > 0:
                result.append({"root": root, "score": score})
        
        result.sort(key=lambda x: x["score"], reverse=True)
        return result
    
    def get_pulse_features_by_root(self, root_name):
        """根据根查询脉象特征"""
        if not self.connected:
            return self._get_default_pulse_features(root_name)
        
        try:
            with self.driver.session() as session:
                result = session.execute_read(self._match_pulse_features_full, root_name)
                return result
        except Exception as e:
            print(f"查询脉象特征失败: {e}")
            return self._get_default_pulse_features(root_name)
    
    def _match_pulse_features_full(self, tx, root_name):
        """匹配根的完整脉象特征"""
        query = """
            MATCH (r:Root {name: $root_name})-[:HAS_PULSE_FEATURE]->(pf)
            RETURN pf.state as state, pf.pulse_position as pulse_position, 
                   pf.pulse_power as pulse_power, pf.pulse_length as pulse_length,
                   pf.pulse_width as pulse_width, pf.palpation_feeling as palpation_feeling,
                   pf.rhythm as rhythm, pf.type as type, pf.value as value
        """
        result = tx.run(query, root_name=root_name)
        return [dict(record) for record in result]
    
    def _match_pulse_features(self, tx, root_name):
        """匹配根的脉象特征（兼容旧接口）"""
        query = """
            MATCH (r:Root {name: $root_name})-[:HAS_PULSE_FEATURE]->(p:PulseFeature)
            RETURN p.type as type, p.value as value
        """
        result = tx.run(query, root_name=root_name)
        return [dict(record) for record in result]
    
    def _get_default_pulse_features(self, root_name):
        """获取默认的脉象特征"""
        default_features = {
            "赫依": [
                {"type": "length", "value": "偏短"},
                {"type": "width", "value": "偏细"},
                {"type": "rhythm", "value": "不匀"}
            ],
            "希拉": [
                {"type": "length", "value": "偏长"},
                {"type": "width", "value": "偏宽"},
                {"type": "rhythm", "value": "快速匀整"}
            ],
            "巴达干": [
                {"type": "length", "value": "偏短"},
                {"type": "width", "value": "偏宽"},
                {"type": "rhythm", "value": "缓慢匀整"}
            ]
        }
        return default_features.get(root_name, [])
    
    def get_signs_by_root(self, root_name):
        """根据根查询体征（体感、舌象、气味）"""
        if not self.connected:
            return self._get_default_signs(root_name)
        
        try:
            with self.driver.session() as session:
                result = session.execute_read(self._match_signs, root_name)
                return result
        except Exception as e:
            print(f"查询体征失败: {e}")
            return self._get_default_signs(root_name)
    
    def _match_signs(self, tx, root_name):
        """匹配根的体征"""
        query = """
            MATCH (r:Root {name: $root_name})-[:HAS_SIGN]->(s)
            RETURN s.type as type, s.content as content
            ORDER BY s.type
        """
        result = tx.run(query, root_name=root_name)
        return [dict(record) for record in result]
    
    def _get_default_signs(self, root_name):
        """获取默认体征"""
        return []
    
    def get_physical_signs_by_root(self, root_name):
        """根据根查询二便表现、精神状态、伴随体征"""
        if not self.connected:
            return self._get_default_physical_signs(root_name)
        
        try:
            with self.driver.session() as session:
                result = session.execute_read(self._match_physical_signs, root_name)
                return result
        except Exception as e:
            print(f"查询二便体征失败: {e}")
            return self._get_default_physical_signs(root_name)
    
    def _match_physical_signs(self, tx, root_name):
        """匹配根的二便体征"""
        query = """
            MATCH (r:Root {name: $root_name})-[:HAS_PHYSICAL_SIGN]->(ps)
            RETURN ps.type as type, ps.content as content
            ORDER BY ps.type
        """
        result = tx.run(query, root_name=root_name)
        return [dict(record) for record in result]
    
    def _get_default_physical_signs(self, root_name):
        """获取默认二便体征"""
        return []
    
    def get_treatments_by_root(self, root_name):
        """根据根查询调理方法"""
        if not self.connected:
            return self._get_default_treatments(root_name)
        
        try:
            with self.driver.session() as session:
                result = session.execute_read(self._match_treatments, root_name)
                return result
        except Exception as e:
            print(f"查询调理方法失败: {e}")
            return self._get_default_treatments(root_name)
    
    def get_inference_path(self, symptoms):
        """获取症状到体质的推理路径"""
        if not self.connected:
            return self._get_default_inference_path(symptoms)
        
        try:
            with self.driver.session() as session:
                result = session.execute_read(self._match_inference_path, symptoms)
                return result
        except Exception as e:
            print(f"获取推理路径失败: {e}")
            return self._get_default_inference_path(symptoms)
    
    def _match_inference_path(self, tx, symptoms):
        """匹配症状到体质的推理路径"""
        query = """
            MATCH path = (s:Symptom)-[:RELATED_TO]->(r:Root)-[:HAS_TREATMENT]->(t:Treatment)
            WHERE s.name IN $symptoms
            WITH path, s, r, t, count(DISTINCT s) as score
            ORDER BY score DESC
            LIMIT 10
            RETURN 
                [node in nodes(path) | {name: node.name, labels: labels(node), description: node.description}] as nodes,
                [rel in relationships(path) | {type: type(rel)}] as relationships,
                r.name as root,
                score
        """
        result = tx.run(query, symptoms=symptoms)
        return [dict(record) for record in result]
    
    def _get_default_inference_path(self, symptoms):
        """获取默认的推理路径"""
        heyi_symptoms = ["心慌", "失眠", "手脚麻", "头晕", "肢体麻木", "胸闷胁胀", "烦躁不安", "易惊易醒", "注意力不集中", "乏力", "气短"]
        xila_symptoms = ["口干", "口苦", "心烦", "目赤肿痛", "胸胁灼痛", "肢体烦热", "急躁易怒", "面红目赤", "失眠多梦", "语声洪亮"]
        badagan_symptoms = ["怕冷", "消化慢", "纳差", "脘腹隐痛", "肢体欠温", "嗜睡", "精神不振", "情绪低落", "少言寡语", "面色萎黄"]
        
        treatments = {
            "赫依": [
                {"name": "饮食调理", "description": "食用温热、易消化的食物"},
                {"name": "起居调理", "description": "保持规律作息，避免过度劳累"},
                {"name": "情志调理", "description": "保持心情平和，避免情绪波动"}
            ],
            "希拉": [
                {"name": "饮食调理", "description": "食用清凉、清淡的食物"},
                {"name": "起居调理", "description": "避免高温环境，保持室内凉爽"},
                {"name": "情志调理", "description": "保持心情舒畅，避免急躁易怒"}
            ],
            "巴达干": [
                {"name": "饮食调理", "description": "食用温热、辛辣的食物"},
                {"name": "起居调理", "description": "保持温暖，避免寒冷环境"},
                {"name": "情志调理", "description": "保持积极乐观的心态"}
            ]
        }
        
        roots = {
            "赫依": {"description": "气，主导精神活动和生命机能"},
            "希拉": {"description": "火，主导消化和代谢功能"},
            "巴达干": {"description": "水和土，主导营养和生长功能"}
        }
        
        paths = []
        seen = set()
        
        for symptom in symptoms:
            if symptom in heyi_symptoms:
                root_name = "赫依"
            elif symptom in xila_symptoms:
                root_name = "希拉"
            elif symptom in badagan_symptoms:
                root_name = "巴达干"
            else:
                continue
            
            for treatment in treatments[root_name]:
                path_key = f"{symptom}-{root_name}-{treatment['name']}"
                if path_key not in seen:
                    seen.add(path_key)
                    paths.append({
                        "nodes": [
                            {"name": symptom, "labels": ["Symptom"], "description": f"{symptom}症状"},
                            {"name": root_name, "labels": ["Root"], "description": roots[root_name]["description"]},
                            {"name": treatment["name"], "labels": ["Treatment"], "description": treatment["description"]}
                        ],
                        "relationships": ["RELATED_TO", "HAS_TREATMENT"],
                        "root": root_name,
                        "score": 1
                    })
        
        return paths
    
    def get_graph_nodes_and_edges(self):
        """获取知识图谱的节点和边数据"""
        if not self.connected:
            return self._get_default_graph_data()
        
        try:
            with self.driver.session() as session:
                result = session.execute_read(self._get_all_nodes_and_edges)
                return result
        except Exception as e:
            print(f"获取图谱数据失败: {e}")
            return self._get_default_graph_data()
    
    def _get_all_nodes_and_edges(self, tx):
        """获取所有节点和边"""
        node_query = """
            MATCH (n)
            RETURN 
                CASE 
                    WHEN 'Root' IN labels(n) THEN n.name 
                    WHEN 'Symptom' IN labels(n) THEN n.name 
                    WHEN 'Treatment' IN labels(n) THEN n.name 
                    WHEN 'PulseFeature' IN labels(n) THEN COALESCE(n.state, n.type + ':' + n.value)
                    WHEN 'Sign' IN labels(n) THEN n.type + ': ' + SUBSTRING(n.content, 0, 20)
                    WHEN 'PhysicalSign' IN labels(n) THEN n.type + ': ' + SUBSTRING(n.content, 0, 20)
                    ELSE 'Unknown'
                END as name,
                labels(n) as labels,
                COALESCE(n.description, n.content, n.state, '') as description
        """
        edge_query = """
            MATCH (a)-[r]->(b)
            RETURN 
                CASE 
                    WHEN 'Root' IN labels(a) THEN a.name 
                    WHEN 'Symptom' IN labels(a) THEN a.name 
                    WHEN 'Treatment' IN labels(a) THEN a.name 
                    WHEN 'PulseFeature' IN labels(a) THEN COALESCE(a.state, a.type + ':' + a.value)
                    WHEN 'Sign' IN labels(a) THEN a.type + ': ' + SUBSTRING(a.content, 0, 20)
                    WHEN 'PhysicalSign' IN labels(a) THEN a.type + ': ' + SUBSTRING(a.content, 0, 20)
                    ELSE 'Unknown'
                END as source,
                CASE 
                    WHEN 'Root' IN labels(b) THEN b.name 
                    WHEN 'Symptom' IN labels(b) THEN b.name 
                    WHEN 'Treatment' IN labels(b) THEN b.name 
                    WHEN 'PulseFeature' IN labels(b) THEN COALESCE(b.state, b.type + ':' + b.value)
                    WHEN 'Sign' IN labels(b) THEN b.type + ': ' + SUBSTRING(b.content, 0, 20)
                    WHEN 'PhysicalSign' IN labels(b) THEN b.type + ': ' + SUBSTRING(b.content, 0, 20)
                    ELSE 'Unknown'
                END as target,
                type(r) as relationship
        """
        
        nodes_result = tx.run(node_query)
        edges_result = tx.run(edge_query)
        
        return {
            "nodes": [dict(record) for record in nodes_result],
            "edges": [dict(record) for record in edges_result]
        }
    
    def _get_default_graph_data(self):
        """获取默认的图谱数据"""
        return {
            "nodes": [
                {"name": "赫依", "labels": ["Root"], "description": "气，主导精神活动和生命机能"},
                {"name": "希拉", "labels": ["Root"], "description": "火，主导消化和代谢功能"},
                {"name": "巴达干", "labels": ["Root"], "description": "水和土，主导营养和生长功能"},
                {"name": "心慌", "labels": ["Symptom"], "description": "心跳加快，心悸不安"},
                {"name": "失眠", "labels": ["Symptom"], "description": "难以入睡或睡眠质量差"},
                {"name": "手脚麻木", "labels": ["Symptom"], "description": "手脚感觉异常，麻木不仁"},
                {"name": "口干", "labels": ["Symptom"], "description": "口腔干燥，口渴多饮"},
                {"name": "口苦", "labels": ["Symptom"], "description": "口中有苦味"},
                {"name": "心烦", "labels": ["Symptom"], "description": "心情烦躁，易怒"},
                {"name": "怕冷", "labels": ["Symptom"], "description": "容易感到寒冷"},
                {"name": "腹胀", "labels": ["Symptom"], "description": "腹部胀满不适"},
                {"name": "腹泻", "labels": ["Symptom"], "description": "大便稀溏，次数增多"},
                {"name": "饮食调理", "labels": ["Treatment"], "description": "饮食方面的调理方法"},
                {"name": "起居调理", "labels": ["Treatment"], "description": "生活起居方面的调理方法"},
                {"name": "情志调理", "labels": ["Treatment"], "description": "情绪心理方面的调理方法"}
            ],
            "edges": [
                {"source": "心慌", "target": "赫依", "relationship": "RELATED_TO"},
                {"source": "失眠", "target": "赫依", "relationship": "RELATED_TO"},
                {"source": "手脚麻木", "target": "赫依", "relationship": "RELATED_TO"},
                {"source": "口干", "target": "希拉", "relationship": "RELATED_TO"},
                {"source": "口苦", "target": "希拉", "relationship": "RELATED_TO"},
                {"source": "心烦", "target": "希拉", "relationship": "RELATED_TO"},
                {"source": "怕冷", "target": "巴达干", "relationship": "RELATED_TO"},
                {"source": "腹胀", "target": "巴达干", "relationship": "RELATED_TO"},
                {"source": "腹泻", "target": "巴达干", "relationship": "RELATED_TO"},
                {"source": "赫依", "target": "饮食调理", "relationship": "HAS_TREATMENT"},
                {"source": "赫依", "target": "起居调理", "relationship": "HAS_TREATMENT"},
                {"source": "赫依", "target": "情志调理", "relationship": "HAS_TREATMENT"},
                {"source": "希拉", "target": "饮食调理", "relationship": "HAS_TREATMENT"},
                {"source": "希拉", "target": "起居调理", "relationship": "HAS_TREATMENT"},
                {"source": "希拉", "target": "情志调理", "relationship": "HAS_TREATMENT"},
                {"source": "巴达干", "target": "饮食调理", "relationship": "HAS_TREATMENT"},
                {"source": "巴达干", "target": "起居调理", "relationship": "HAS_TREATMENT"},
                {"source": "巴达干", "target": "情志调理", "relationship": "HAS_TREATMENT"}
            ]
        }
    
    def _match_treatments(self, tx, root_name):
        """匹配根的调理方法"""
        query = """
            MATCH (r:Root {name: $root_name})-[:HAS_TREATMENT]->(t:Treatment)
            RETURN t.name as name, t.description as description
        """
        result = tx.run(query, root_name=root_name)
        return [dict(record) for record in result]
    
    def _get_default_treatments(self, root_name):
        """获取默认的调理方法"""
        default_treatments = {
            "赫依": [
                {"name": "饮食调理", "description": "食用温热、易消化的食物"},
                {"name": "起居调理", "description": "保持规律作息，避免过度劳累"},
                {"name": "情志调理", "description": "保持心情平和，避免情绪波动"}
            ],
            "希拉": [
                {"name": "饮食调理", "description": "食用清凉、清淡的食物"},
                {"name": "起居调理", "description": "避免高温环境，保持室内凉爽"},
                {"name": "情志调理", "description": "保持心情舒畅，避免急躁易怒"}
            ],
            "巴达干": [
                {"name": "饮食调理", "description": "食用温热、辛辣的食物"},
                {"name": "起居调理", "description": "保持温暖，避免寒冷环境"},
                {"name": "情志调理", "description": "保持积极乐观的心态"}
            ]
        }
        return default_treatments.get(root_name, [])

try:
    graph = KnowledgeGraph(
        NEO4J_CONFIG["uri"],
        NEO4J_CONFIG["user"],
        NEO4J_CONFIG["password"]
    )
except Exception as e:
    print(f"创建知识图谱实例失败: {e}")
    class MockKnowledgeGraph:
        def get_root_by_symptoms(self, symptoms):
            heyi_symptoms = ["心慌", "失眠", "手脚麻木", "头晕", "胸闷"]
            xila_symptoms = ["口干", "口苦", "心烦", "目赤", "喜冷饮"]
            badagan_symptoms = ["怕冷", "腹胀", "腹泻", "痰多清稀", "口淡"]
            
            scores = {"赫依": 0, "希拉": 0, "巴达干": 0}
            for symptom in symptoms:
                if symptom in heyi_symptoms:
                    scores["赫依"] += 1
                elif symptom in xila_symptoms:
                    scores["希拉"] += 1
                elif symptom in badagan_symptoms:
                    scores["巴达干"] += 1
            
            result = []
            for root, score in scores.items():
                if score > 0:
                    result.append({"root": root, "score": score})
            result.sort(key=lambda x: x["score"], reverse=True)
            return result
        
        def get_pulse_features_by_root(self, root_name):
            defaults = {
                "赫依": [{"type": "length", "value": "偏短"}, {"type": "width", "value": "偏细"}, {"type": "rhythm", "value": "不匀"}],
                "希拉": [{"type": "length", "value": "偏长"}, {"type": "width", "value": "偏宽"}, {"type": "rhythm", "value": "快速匀整"}],
                "巴达干": [{"type": "length", "value": "偏短"}, {"type": "width", "value": "偏宽"}, {"type": "rhythm", "value": "缓慢匀整"}]
            }
            return defaults.get(root_name, [])
        
        def get_signs_by_root(self, root_name):
            return []
        
        def get_physical_signs_by_root(self, root_name):
            return []
        
        def get_treatments_by_root(self, root_name):
            defaults = {
                "赫依": [{"name": "饮食调理", "description": "食用温热、易消化的食物"}, {"name": "起居调理", "description": "保持规律作息，避免过度劳累"}, {"name": "情志调理", "description": "保持心情平和，避免情绪波动"}],
                "希拉": [{"name": "饮食调理", "description": "食用清凉、清淡的食物"}, {"name": "起居调理", "description": "避免高温环境，保持室内凉爽"}, {"name": "情志调理", "description": "保持心情舒畅，避免急躁易怒"}],
                "巴达干": [{"name": "饮食调理", "description": "食用温热、辛辣的食物"}, {"name": "起居调理", "description": "保持温暖，避免寒冷环境"}, {"name": "情志调理", "description": "保持积极乐观的心态"}]
            }
            return defaults.get(root_name, [])
        
        def get_inference_path(self, symptoms):
            heyi_symptoms = ["心慌", "失眠", "手脚麻", "头晕", "肢体麻木", "胸闷胁胀", "烦躁不安", "易惊易醒", "注意力不集中", "乏力", "气短"]
            xila_symptoms = ["口干", "口苦", "心烦", "目赤肿痛", "胸胁灼痛", "肢体烦热", "急躁易怒", "面红目赤", "失眠多梦", "语声洪亮"]
            badagan_symptoms = ["怕冷", "消化慢", "纳差", "脘腹隐痛", "肢体欠温", "嗜睡", "精神不振", "情绪低落", "少言寡语", "面色萎黄"]
            
            treatments = {
                "赫依": [
                    {"name": "饮食调理", "description": "食用温热、易消化的食物"},
                    {"name": "起居调理", "description": "保持规律作息，避免过度劳累"},
                    {"name": "情志调理", "description": "保持心情平和，避免情绪波动"}
                ],
                "希拉": [
                    {"name": "饮食调理", "description": "食用清凉、清淡的食物"},
                    {"name": "起居调理", "description": "避免高温环境，保持室内凉爽"},
                    {"name": "情志调理", "description": "保持心情舒畅，避免急躁易怒"}
                ],
                "巴达干": [
                    {"name": "饮食调理", "description": "食用温热、辛辣的食物"},
                    {"name": "起居调理", "description": "保持温暖，避免寒冷环境"},
                    {"name": "情志调理", "description": "保持积极乐观的心态"}
                ]
            }
            
            roots = {
                "赫依": {"description": "气，主导精神活动和生命机能"},
                "希拉": {"description": "火，主导消化和代谢功能"},
                "巴达干": {"description": "水和土，主导营养和生长功能"}
            }
            
            paths = []
            seen = set()
            
            for symptom in symptoms:
                if symptom in heyi_symptoms:
                    root_name = "赫依"
                elif symptom in xila_symptoms:
                    root_name = "希拉"
                elif symptom in badagan_symptoms:
                    root_name = "巴达干"
                else:
                    continue
                
                for treatment in treatments[root_name]:
                    path_key = f"{symptom}-{root_name}-{treatment['name']}"
                    if path_key not in seen:
                        seen.add(path_key)
                        paths.append({
                            "nodes": [
                                {"name": symptom, "labels": ["Symptom"], "description": f"{symptom}症状"},
                                {"name": root_name, "labels": ["Root"], "description": roots[root_name]["description"]},
                                {"name": treatment["name"], "labels": ["Treatment"], "description": treatment["description"]}
                            ],
                            "relationships": ["RELATED_TO", "HAS_TREATMENT"],
                            "root": root_name,
                            "score": 1
                        })
            
            return paths
        
        def get_graph_nodes_and_edges(self):
            return {
                "nodes": [
                    {"name": "赫依", "labels": ["Root"], "description": "气，主导精神活动和生命机能"},
                    {"name": "希拉", "labels": ["Root"], "description": "火，主导消化和代谢功能"},
                    {"name": "巴达干", "labels": ["Root"], "description": "水和土，主导营养和生长功能"},
                    {"name": "心慌", "labels": ["Symptom"], "description": "心跳加快，心悸不安"},
                    {"name": "失眠", "labels": ["Symptom"], "description": "难以入睡或睡眠质量差"},
                    {"name": "手脚麻木", "labels": ["Symptom"], "description": "手脚感觉异常，麻木不仁"},
                    {"name": "口干", "labels": ["Symptom"], "description": "口腔干燥，口渴多饮"},
                    {"name": "口苦", "labels": ["Symptom"], "description": "口中有苦味"},
                    {"name": "心烦", "labels": ["Symptom"], "description": "心情烦躁，易怒"},
                    {"name": "怕冷", "labels": ["Symptom"], "description": "容易感到寒冷"},
                    {"name": "腹胀", "labels": ["Symptom"], "description": "腹部胀满不适"},
                    {"name": "腹泻", "labels": ["Symptom"], "description": "大便稀溏，次数增多"},
                    {"name": "饮食调理", "labels": ["Treatment"], "description": "饮食方面的调理方法"},
                    {"name": "起居调理", "labels": ["Treatment"], "description": "生活起居方面的调理方法"},
                    {"name": "情志调理", "labels": ["Treatment"], "description": "情绪心理方面的调理方法"}
                ],
                "edges": [
                    {"source": "心慌", "target": "赫依", "relationship": "RELATED_TO"},
                    {"source": "失眠", "target": "赫依", "relationship": "RELATED_TO"},
                    {"source": "手脚麻木", "target": "赫依", "relationship": "RELATED_TO"},
                    {"source": "口干", "target": "希拉", "relationship": "RELATED_TO"},
                    {"source": "口苦", "target": "希拉", "relationship": "RELATED_TO"},
                    {"source": "心烦", "target": "希拉", "relationship": "RELATED_TO"},
                    {"source": "怕冷", "target": "巴达干", "relationship": "RELATED_TO"},
                    {"source": "腹胀", "target": "巴达干", "relationship": "RELATED_TO"},
                    {"source": "腹泻", "target": "巴达干", "relationship": "RELATED_TO"},
                    {"source": "赫依", "target": "饮食调理", "relationship": "HAS_TREATMENT"},
                    {"source": "赫依", "target": "起居调理", "relationship": "HAS_TREATMENT"},
                    {"source": "赫依", "target": "情志调理", "relationship": "HAS_TREATMENT"},
                    {"source": "希拉", "target": "饮食调理", "relationship": "HAS_TREATMENT"},
                    {"source": "希拉", "target": "起居调理", "relationship": "HAS_TREATMENT"},
                    {"source": "希拉", "target": "情志调理", "relationship": "HAS_TREATMENT"},
                    {"source": "巴达干", "target": "饮食调理", "relationship": "HAS_TREATMENT"},
                    {"source": "巴达干", "target": "起居调理", "relationship": "HAS_TREATMENT"},
                    {"source": "巴达干", "target": "情志调理", "relationship": "HAS_TREATMENT"}
                ]
            }
    
    graph = MockKnowledgeGraph()
    print("使用模拟知识图谱实例")

def init_knowledge_graph():
    """初始化知识图谱"""
    if not KG_CONFIG["auto_init"]:
        print("知识图谱自动初始化已禁用")
        return False
    
    try:
        if hasattr(graph, 'create_three_roots_model'):
            return graph.create_three_roots_model()
        else:
            print("知识图谱实例不支持初始化")
            return False
    except Exception as e:
        print(f"知识图谱初始化失败: {e}")
        return False

def get_knowledge_graph():
    """获取知识图谱实例"""
    return graph