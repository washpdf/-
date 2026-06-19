# mengyi_diagnosis_service.py
# 整合了知识图谱构建、GNN推理、多模态特征融合的完整诊断服务

from flask import Flask, request, jsonify
from flask_cors import CORS
import json
from collections import defaultdict
import base64
from io import BytesIO
from PIL import Image
import re

app = Flask(__name__)
CORS(app)  # 允许前端跨域调用

# ==================== 第一部分：知识图谱构建 ====================

class MengyiKnowledgeGraph:
    """蒙医三根知识图谱"""
    
    def __init__(self):
        self.nodes = {}
        self.edges = []
        self.adjacency = defaultdict(list)
        self._build()
    
    def _build(self):
        # 8种证型节点
        constitution_data = [
            {"id": "赫依_偏盛", "root": "赫依", "state": "偏盛", 
             "pulse": {"length": "偏短", "width": "偏细", "rhythm": "不匀"},
             "symptoms": ["心慌", "失眠", "手脚麻", "头晕", "胸闷", "肢体麻木", "烦躁不安", "易惊"]},
            
            {"id": "赫依_平衡", "root": "赫依", "state": "平衡",
             "pulse": {"length": "适中", "width": "适中", "rhythm": "均匀"},
             "symptoms": ["无不适", "气机顺畅", "精神平和"]},
            
            {"id": "赫依_偏衰", "root": "赫依", "state": "偏衰",
             "pulse": {"length": "偏短", "width": "偏细", "rhythm": "稍慢"},
             "symptoms": ["乏力", "气短", "懒动", "腰膝酸软", "汗出", "语声低微"]},
            
            {"id": "希拉_偏盛", "root": "希拉", "state": "偏盛",
             "pulse": {"length": "偏长", "width": "偏宽", "rhythm": "快速匀整"},
             "symptoms": ["口干", "口苦", "心烦", "目赤", "喜冷饮", "脸红", "烦躁易怒"]},
            
            {"id": "希拉_平衡", "root": "希拉", "state": "平衡",
             "pulse": {"length": "适中", "width": "适中", "rhythm": "均匀"},
             "symptoms": ["消化正常", "心情平和", "口苦不显"]},
            
            {"id": "希拉_偏衰", "root": "希拉", "state": "偏衰",
             "pulse": {"length": "偏短", "width": "偏细", "rhythm": "稍慢"},
             "symptoms": ["怕冷", "消化慢", "脘腹隐痛", "喜温喜按"]},
            
            {"id": "巴达干_偏盛", "root": "巴达干", "state": "偏盛",
             "pulse": {"length": "偏短", "width": "偏宽", "rhythm": "缓慢匀整"},
             "symptoms": ["怕冷", "腹胀", "腹泻", "痰多清稀", "口淡", "嗜睡"]},
            
            {"id": "巴达干_平衡", "root": "巴达干", "state": "平衡",
             "pulse": {"length": "适中", "width": "适中", "rhythm": "均匀"},
             "symptoms": ["津液充足", "消化平稳", "痰多不显"]}
        ]
        
        # 添加证型节点和症状边
        for item in constitution_data:
            node_id = item["id"]
            self.nodes[node_id] = {
                "type": "constitution",
                "root": item["root"],
                "state": item["state"],
                "pulse": item["pulse"]
            }
            
            for symptom in item["symptoms"]:
                symptom_id = f"症状_{symptom}"
                if symptom_id not in self.nodes:
                    self.nodes[symptom_id] = {"type": "symptom", "name": symptom}
                self._add_edge(symptom_id, node_id, "indicates", 2.0)
        
        # 脉象特征节点
        pulse_mappings = {
            "脉长_偏短": ["赫依_偏盛", "赫依_偏衰", "希拉_偏衰", "巴达干_偏盛"],
            "脉长_适中": ["赫依_平衡", "希拉_平衡", "巴达干_平衡"],
            "脉长_偏长": ["希拉_偏盛"],
            "脉宽_偏细": ["赫依_偏盛", "赫依_偏衰", "希拉_偏衰"],
            "脉宽_适中": ["赫依_平衡", "希拉_平衡", "巴达干_平衡"],
            "脉宽_偏宽": ["希拉_偏盛", "巴达干_偏盛"],
            "节律_不匀": ["赫依_偏盛"],
            "节律_均匀": ["赫依_平衡", "希拉_平衡", "巴达干_平衡"],
            "节律_快速匀整": ["希拉_偏盛"],
            "节律_缓慢匀整": ["巴达干_偏盛"],
            "节律_稍慢": ["赫依_偏衰", "希拉_偏衰"],
        }
        
        for pulse_feature, targets in pulse_mappings.items():
            node_id = f"脉象_{pulse_feature}"
            if node_id not in self.nodes:
                self.nodes[node_id] = {"type": "pulse_feature", "name": pulse_feature}
            for target in targets:
                self._add_edge(node_id, target, "matches", 1.5)
        
        # 舌象特征节点
        tongue_mappings = {
            "舌质_淡": ["赫依_偏盛", "赫依_偏衰", "巴达干_偏盛"],
            "舌质_淡红": ["赫依_平衡", "希拉_平衡", "巴达干_平衡"],
            "舌质_红": ["希拉_偏盛"],
            "苔_薄白": ["赫依_平衡", "赫依_偏盛"],
            "苔_薄黄": ["希拉_平衡"],
            "苔_黄腻": ["希拉_偏盛"],
            "苔_白厚腻": ["巴达干_偏盛"],
            "舌体_胖": ["赫依_偏衰", "巴达干_偏盛"],
            "舌体_适中": ["赫依_平衡", "希拉_平衡", "巴达干_平衡"],
        }
        
        for tongue_feature, targets in tongue_mappings.items():
            node_id = f"舌象_{tongue_feature}"
            if node_id not in self.nodes:
                self.nodes[node_id] = {"type": "tongue_feature", "name": tongue_feature}
            for target in targets:
                self._add_edge(node_id, target, "indicates", 1.5)
        
        # 三根相互影响
        self._add_edge("赫依_偏盛", "希拉_偏盛", "aggravates", 0.5)
        self._add_edge("希拉_偏盛", "赫依_偏盛", "aggravates", 0.3)
        
        print(f"知识图谱构建完成: {len(self.nodes)}节点, {len(self.edges)}边")
    
    def _add_edge(self, source, target, relation, weight):
        self.edges.append((source, target, relation, weight))
        self.adjacency[source].append((target, relation, weight))
    
    def get_neighbors(self, node_id):
        return self.adjacency.get(node_id, [])
    
    def get_node(self, node_id):
        return self.nodes.get(node_id)


# ==================== 第二部分：推理引擎 ====================

class DiagnosisEngine:
    """基于知识图谱的诊断推理引擎"""
    
    def __init__(self, kg):
        self.kg = kg
    
    def extract_tongue_features(self, tongue_text):
        """从舌象文本提取特征"""
        features = []
        text = tongue_text.lower()
        
        feature_map = {
            "舌质_淡": ["淡", "淡白"],
            "舌质_淡红": ["淡红"],
            "舌质_红": ["红", "鲜红"],
            "苔_薄白": ["薄白"],
            "苔_薄黄": ["薄黄"],
            "苔_黄腻": ["黄腻"],
            "苔_白厚腻": ["白厚", "厚腻"],
            "舌体_胖": ["胖", "胖大"],
            "舌体_适中": ["适中", "正常"],
        }
        
        for feature, keywords in feature_map.items():
            for kw in keywords:
                if kw in text:
                    features.append(feature)
                    break
        
        return features if features else ["舌质_淡红", "苔_薄白", "舌体_适中"]
    
    def extract_pulse_features(self, pulse_text):
        """从脉象文本提取特征"""
        features = []
        text = pulse_text.lower()
        
        feature_map = {
            "脉长_偏短": ["偏短", "短"],
            "脉长_适中": ["适中"],
            "脉长_偏长": ["偏长", "长"],
            "脉宽_偏细": ["偏细", "细"],
            "脉宽_适中": ["适中"],
            "脉宽_偏宽": ["偏宽", "宽"],
            "节律_不匀": ["不匀", "不齐", "歇止"],
            "节律_均匀": ["均匀", "规整"],
            "节律_快速匀整": ["快速", "洪数"],
            "节律_缓慢匀整": ["缓慢", "迟缓"],
            "节律_稍慢": ["稍慢"],
        }
        
        for feature, keywords in feature_map.items():
            for kw in keywords:
                if kw in text:
                    features.append(feature)
                    break
        
        return features if features else ["脉长_适中", "脉宽_适中", "节律_均匀"]
    
    def extract_symptom_features(self, symptom_text):
        """从症状描述提取特征"""
        features = []
        symptom_list = ["心慌", "失眠", "手脚麻", "头晕", "胸闷", "口干", "口苦", 
                       "心烦", "目赤", "怕冷", "腹胀", "腹泻", "痰多", "乏力", 
                       "气短", "腰膝酸软", "烦躁", "易惊"]
        
        for symptom in symptom_list:
            if symptom in symptom_text:
                features.append(symptom)
        
        return features
    
    def multi_modal_inference(self, symptoms, pulse_features, tongue_features):
        """多模态融合推理"""
        scores = defaultdict(float)
        
        # 症状推理（权重最高）
        for symptom in symptoms:
            symptom_id = f"症状_{symptom}"
            for neighbor, relation, weight in self.kg.get_neighbors(symptom_id):
                if self.kg.get_node(neighbor) and self.kg.get_node(neighbor).get("type") == "constitution":
                    scores[neighbor] += weight * 1.0
        
        # 脉象推理
        for pulse_feat in pulse_features:
            node_id = f"脉象_{pulse_feat}"
            if node_id in self.kg.nodes:
                for neighbor, relation, weight in self.kg.get_neighbors(node_id):
                    if self.kg.get_node(neighbor) and self.kg.get_node(neighbor).get("type") == "constitution":
                        scores[neighbor] += weight * 0.8
        
        # 舌象推理
        for tongue_feat in tongue_features:
            node_id = f"舌象_{tongue_feat}"
            if node_id in self.kg.nodes:
                for neighbor, relation, weight in self.kg.get_neighbors(node_id):
                    if self.kg.get_node(neighbor) and self.kg.get_node(neighbor).get("type") == "constitution":
                        scores[neighbor] += weight * 0.7
        
        # 归一化到0-100
        if scores:
            max_score = max(scores.values())
            if max_score > 0:
                for node in scores:
                    scores[node] = (scores[node] / max_score) * 100
        
        return dict(sorted(scores.items(), key=lambda x: x[1], reverse=True))
    
    def get_reasoning_path(self, symptoms, pulse_features, tongue_features):
        """生成可解释的推理路径"""
        explanations = []
        
        # 症状路径
        for symptom in symptoms[:3]:
            symptom_id = f"症状_{symptom}"
            for neighbor, relation, weight in self.kg.get_neighbors(symptom_id):
                node_info = self.kg.get_node(neighbor)
                if node_info and node_info.get("type") == "constitution":
                    explanations.append({
                        "type": "symptom",
                        "evidence": symptom,
                        "conclusion": f"{node_info.get('root')}_{node_info.get('state')}",
                        "weight": weight
                    })
                    break
        
        # 脉象路径
        for pulse_feat in pulse_features[:2]:
            node_id = f"脉象_{pulse_feat}"
            if node_id in self.kg.nodes:
                for neighbor, relation, weight in self.kg.get_neighbors(node_id):
                    node_info = self.kg.get_node(neighbor)
                    if node_info and node_info.get("type") == "constitution":
                        explanations.append({
                            "type": "pulse",
                            "evidence": pulse_feat.replace("_", "、"),
                            "conclusion": f"{node_info.get('root')}_{node_info.get('state')}",
                            "weight": weight
                        })
                        break
        
        return explanations[:5]  # 返回前5条推理路径


# ==================== 第三部分：Flask API服务 ====================

# 初始化知识图谱和推理引擎
kg = MengyiKnowledgeGraph()
engine = DiagnosisEngine(kg)

@app.route('/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({"status": "ok", "nodes": len(kg.nodes), "edges": len(kg.edges)})


@app.route('/api/diagnose', methods=['POST'])
def diagnose():
    """
    核心诊断API
    输入: tongue_text, pulse_text, symptom_text
    输出: 三根量化值 + 推理路径
    """
    try:
        data = request.json
        tongue_text = data.get('tongue_text', '')
        pulse_text = data.get('pulse_text', '')
        symptom_text = data.get('symptom_text', '')
        
        # 1. 特征提取
        tongue_features = engine.extract_tongue_features(tongue_text)
        pulse_features = engine.extract_pulse_features(pulse_text)
        symptoms = engine.extract_symptom_features(symptom_text)
        
        # 2. 多模态推理
        inference_result = engine.multi_modal_inference(symptoms, pulse_features, tongue_features)
        
        # 3. 计算三根量化值
        root_scores = {
            "赫依": 0,
            "希拉": 0,
            "巴达干": 0
        }
        
        for node_id, score in inference_result.items():
            node_info = kg.get_node(node_id)
            if node_info and node_info.get("type") == "constitution":
                root = node_info.get("root")
                root_scores[root] = max(root_scores[root], score)
        
        # 4. 确定主要证型
        primary = max(root_scores, key=root_scores.get)
        
        # 5. 获取推理路径
        reasoning = engine.get_reasoning_path(symptoms, pulse_features, tongue_features)
        
        return jsonify({
            "success": True,
            "root_scores": root_scores,
            "primary_root": primary,
            "diagnosis_detail": inference_result,
            "reasoning_path": reasoning,
            "extracted_features": {
                "symptoms": symptoms,
                "pulse_features": pulse_features,
                "tongue_features": tongue_features
            }
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/advice', methods=['POST'])
def generate_advice():
    """
    生成调理建议（基于诊断结果）
    """
    try:
        data = request.json
        root_scores = data.get('root_scores', {})
        primary_root = data.get('primary_root', '')
        
        # 基于三根量化值生成建议
        advice = {
            "赫依": {
                "diet": "推荐温性、滋养食物：小米粥、羊肉汤、红枣、桂圆、核桃",
                "lifestyle": "规律作息，避免熬夜，建议每晚23:00前入睡",
                "emotion": "多听舒缓音乐，练习冥想，保持心情平和",
                "avoid": "避免咖啡、浓茶、熬夜、过度劳累"
            },
            "希拉": {
                "diet": "推荐凉性、清淡食物：绿豆、苦瓜、黄瓜、冬瓜、梨",
                "lifestyle": "保持环境通风凉爽，避免烈日下活动",
                "emotion": "练习深呼吸，避免竞争性强的活动",
                "avoid": "避免辛辣刺激食物，减少酒精摄入"
            },
            "巴达干": {
                "diet": "推荐温热、轻淡食物：姜汤、胡椒、羊肉、洋葱",
                "lifestyle": "早起活动，每天30分钟以上有氧运动",
                "emotion": "多参与社交活动，培养运动型爱好",
                "avoid": "避免油腻甜食，减少寒凉食物"
            }
        }
        
        result = advice.get(primary_root, advice["赫依"])
        result["primary_root"] = primary_root
        result["scores"] = root_scores
        
        return jsonify({"success": True, "advice": result})
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ==================== 启动服务 ====================
if __name__ == '__main__':
    print("\n" + "="*50)
    print("三根智诊服务启动中...")
    print("="*50)
    print(f"知识图谱: {len(kg.nodes)}个节点, {len(kg.edges)}条边")
    print("API地址: http://localhost:5002")
    print("接口列表:")
    print("   GET  /health     - 健康检查")
    print("   POST /api/diagnose - 核心诊断")
    print("   POST /api/advice   - 调理建议")
    print("="*50)
    print("\n请确保前端代码中的 API_BASE_URL 设置为 http://localhost:5002")
    print("="*50 + "\n")
    
    app.run(host='0.0.0.0', port=5002, debug=True)