# app.py

from flask import Flask, request, jsonify, session, send_from_directory
from flask_cors import CORS
import bcrypt
from datetime import datetime, timedelta
from functools import wraps
import pyodbc
import os
import json
import base64
from io import BytesIO
from PIL import Image
import numpy as np

# 导入知识图谱模块
from knowledge_graph import init_knowledge_graph, get_knowledge_graph
# 导入LSTM预测模块
from lstm_prediction import predict_future

app = Flask(__name__)

# 配置

# 初始化知识图谱
try:
    init_knowledge_graph()
except Exception as e:
    print(f"知识图谱初始化失败: {e}")
app.config['SECRET_KEY'] = 'your-secret-key-change-in-production-2024'
app.config['SESSION_COOKIE_NAME'] = 'mongolian_medicine_session'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
app.config['SESSION_REFRESH_EACH_REQUEST'] = True

# CORS 配置
CORS(app,
     origins=['http://localhost:5000', 'http://127.0.0.1:5000', 'http://localhost:5500', 'http://127.0.0.1:5500', 'http://localhost:3000', 'http://127.0.0.1:3000'],
     supports_credentials=True,
     allow_headers=['Content-Type', 'Authorization'],
     methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])

# ==================== 数据库配置 ====================
# 请根据你的 SQL Server 配置修改
DB_SERVER = 'localhost'  # 或 '127.0.0.1'
DB_NAME = 'MongolianMedicineDB'
DB_USERNAME = 'sa'
DB_PASSWORD = '961129Aa!'
DB_DRIVER = '{ODBC Driver 17 for SQL Server}'

DB_CONNECTION_STRING = f"DRIVER={DB_DRIVER};SERVER={DB_SERVER};DATABASE={DB_NAME};UID={DB_USERNAME};PWD={DB_PASSWORD}"

def get_db_connection():
    """获取数据库连接"""
    try:
        conn = pyodbc.connect(DB_CONNECTION_STRING, timeout=30)
        return conn
    except Exception as e:
        print(f"数据库连接失败: {e}")
        return None

# ==================== 数据库操作函数 ====================
def create_user(email, password_hash, name):
    """创建新用户"""
    conn = get_db_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO Users (Email, PasswordHash, Name, CreatedAt)
            VALUES (?, ?, ?, GETDATE())
        """, (email, password_hash, name))
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"创建用户失败: {e}")
        return False

def get_user_by_email(email):
    """根据邮箱获取用户"""
    conn = get_db_connection()
    if not conn:
        return None
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT Id, Email, PasswordHash, Name, CreatedAt, LastLoginAt 
            FROM Users WHERE Email = ?
        """, (email,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        return row
    except Exception as e:
        print(f"查询用户失败: {e}")
        return None

def get_user_by_id(user_id):
    """根据ID获取用户"""
    conn = get_db_connection()
    if not conn:
        return None
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT Id, Email, Name, CreatedAt, LastLoginAt 
            FROM Users WHERE Id = ?
        """, (user_id,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        return row
    except Exception as e:
        print(f"查询用户失败: {e}")
        return None

def update_last_login(user_id):
    """更新最后登录时间"""
    conn = get_db_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE Users SET LastLoginAt = GETDATE() WHERE Id = ?", (user_id,))
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"更新登录时间失败: {e}")
        return False

def save_diagnosis_record(user_id, result, advice):
    """保存诊断记录"""
    conn = get_db_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO DiagnosisRecords (UserId, Result, Advice, CreatedAt)
            VALUES (?, ?, ?, GETDATE())
        """, (user_id, result, advice))
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"保存诊断记录失败: {e}")
        return False

def get_user_diagnosis_history(user_id):
    """获取用户诊断历史"""
    conn = get_db_connection()
    if not conn:
        return []
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT Id, Result, Advice, CreatedAt 
            FROM DiagnosisRecords 
            WHERE UserId = ? 
            ORDER BY CreatedAt DESC
        """, (user_id,))
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        
        history = []
        for row in rows:
            history.append({
                'Id': row[0],
                'Result': row[1],
                'Advice': row[2],
                'CreatedAt': row[3]
            })
        return history
    except Exception as e:
        print(f"获取诊断历史失败: {e}")
        return []

def check_today_regimen(user_id, today_date):
    """检查今日是否已打卡"""
    conn = get_db_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(1) FROM RegimenRecords 
            WHERE UserId = ? AND RecordDate = ?
        """, (user_id, today_date))
        count = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        return count > 0
    except Exception as e:
        print(f"检查打卡失败: {e}")
        return False

def add_regimen_record(user_id, record_date):
    """添加调理打卡记录"""
    conn = get_db_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO RegimenRecords (UserId, RecordDate, CreatedAt)
            VALUES (?, ?, GETDATE())
        """, (user_id, record_date))
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"添加打卡记录失败: {e}")
        return False

def get_regimen_count(user_id):
    """获取用户打卡总数"""
    conn = get_db_connection()
    if not conn:
        return 0
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(1) FROM RegimenRecords WHERE UserId = ?", (user_id,))
        count = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        return count
    except Exception as e:
        print(f"获取打卡数失败: {e}")
        return 0

# ==================== 登录验证装饰器 ====================
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': '请先登录'}), 401
        return f(*args, **kwargs)
    return decorated_function

# ==================== API 路由 ====================

@app.route('/api/auth/register', methods=['POST'])
def register():
    """用户注册"""
    try:
        data = request.get_json()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        name = data.get('name', '').strip()
        
        if not email or not password or not name:
            return jsonify({'success': False, 'message': '请填写完整信息'}), 400
        
        if len(password) < 6:
            return jsonify({'success': False, 'message': '密码长度不能少于6位'}), 400
        
        existing_user = get_user_by_email(email)
        if existing_user:
            return jsonify({'success': False, 'message': '该邮箱已注册'}), 400
        
        salt = bcrypt.gensalt()
        password_hash = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
        
        if create_user(email, password_hash, name):
            user = get_user_by_email(email)
            if user:
                update_last_login(user[0])
                
                session.permanent = True
                session['user_id'] = user[0]
                session['user_email'] = user[1]
                session['user_name'] = user[3]
                
                return jsonify({
                    'success': True,
                    'message': '注册成功！',
                    'auto_login': True,
                    'user': {
                        'id': user[0],
                        'email': user[1],
                        'name': user[3]
                    }
                })
            return jsonify({'success': True, 'message': '注册成功！请登录'})
        else:
            return jsonify({'success': False, 'message': '注册失败，请稍后重试'}), 500
    
    except Exception as e:
        print(f"注册错误: {e}")
        return jsonify({'success': False, 'message': f'注册失败: {str(e)}'}), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    """用户登录"""
    try:
        data = request.get_json()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        
        if not email or not password:
            return jsonify({'success': False, 'message': '请填写邮箱和密码'}), 400
        
        user = get_user_by_email(email)
        if not user:
            return jsonify({'success': False, 'message': '邮箱或密码错误'}), 401
        
        stored_hash = user[2]
        if not bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8')):
            return jsonify({'success': False, 'message': '邮箱或密码错误'}), 401
        
        update_last_login(user[0])
        
        session.permanent = True
        session['user_id'] = user[0]
        session['user_email'] = user[1]
        session['user_name'] = user[3]
        
        return jsonify({
            'success': True,
            'message': '登录成功',
            'user': {
                'id': user[0],
                'email': user[1],
                'name': user[3]
            }
        })
    
    except Exception as e:
        print(f"登录错误: {e}")
        return jsonify({'success': False, 'message': f'登录失败: {str(e)}'}), 500

@app.route('/api/auth/logout', methods=['POST'])
def logout():
    """退出登录"""
    session.clear()
    return jsonify({'success': True, 'message': '已退出登录'})

@app.route('/api/auth/session', methods=['GET'])
def get_session():
    """获取当前会话"""
    if 'user_id' in session:
        return jsonify({
            'success': True,
            'user': {
                'id': session['user_id'],
                'email': session.get('user_email'),
                'name': session.get('user_name')
            }
        })
    return jsonify({'success': False, 'message': '未登录'})

@app.route('/api/diagnosis/save', methods=['POST'])
@login_required
def save_diagnosis():
    """保存诊断记录"""
    try:
        data = request.get_json()
        result = data.get('result', '')
        advice = data.get('advice', '')
        
        if not result:
            return jsonify({'success': False, 'message': '诊断结果不能为空'}), 400
        
        if save_diagnosis_record(session['user_id'], result, advice):
            return jsonify({'success': True, 'message': '诊断记录已保存'})
        else:
            return jsonify({'success': False, 'message': '保存失败'}), 500
    
    except Exception as e:
        print(f"保存诊断错误: {e}")
        return jsonify({'success': False, 'message': f'保存失败: {str(e)}'}), 500

@app.route('/api/diagnosis/history', methods=['GET'])
@login_required
def get_diagnosis_history():
    """获取用户诊断历史"""
    try:
        records = get_user_diagnosis_history(session['user_id'])
        
        history = []
        for record in records:
            history.append({
                'id': record['Id'],
                'result': record['Result'],
                'advice': record['Advice'],
                'created_at': record['CreatedAt'].isoformat() if record['CreatedAt'] else None
            })
        
        return jsonify({'success': True, 'history': history})
    
    except Exception as e:
        print(f"获取历史错误: {e}")
        return jsonify({'success': False, 'message': f'获取失败: {str(e)}'}), 500

@app.route('/api/regimen/check', methods=['GET'])
@login_required
def check_regimen_today():
    """检查今日是否已打卡"""
    try:
        today_str = datetime.now().date().isoformat()
        has_record = check_today_regimen(session['user_id'], today_str)
        return jsonify({'success': True, 'hasRecord': has_record})
    except Exception as e:
        print(f"检查打卡错误: {e}")
        return jsonify({'success': False, 'message': f'检查失败: {str(e)}'}), 500

@app.route('/api/regimen/record', methods=['POST'])
@login_required
def add_regimen():
    """添加调理打卡记录"""
    try:
        today_str = datetime.now().date().isoformat()
        
        if check_today_regimen(session['user_id'], today_str):
            return jsonify({'success': False, 'message': '今日已打卡'}), 400
        
        if add_regimen_record(session['user_id'], today_str):
            total_count = get_regimen_count(session['user_id'])
            return jsonify({
                'success': True,
                'message': '打卡成功！',
                'totalCount': total_count
            })
        else:
            return jsonify({'success': False, 'message': '打卡失败'}), 500
    
    except Exception as e:
        print(f"打卡错误: {e}")
        return jsonify({'success': False, 'message': f'打卡失败: {str(e)}'}), 500

@app.route('/api/tongue/validate', methods=['POST'])
def validate_tongue_image():
    """验证上传的图片是否为舌象图片"""
    try:
        data = request.get_json()
        image_base64 = data.get('image', '')
        
        if not image_base64:
            return jsonify({'success': False, 'message': '未提供图片', 'is_tongue': False}), 400
        
        if 'base64,' in image_base64:
            image_base64 = image_base64.split('base64,')[1]
        
        image_data = base64.b64decode(image_base64)
        image = Image.open(BytesIO(image_data))
        
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        img_array = np.array(image)
        
        red_channel = img_array[:, :, 0].astype(float)
        green_channel = img_array[:, :, 1].astype(float)
        blue_channel = img_array[:, :, 2].astype(float)
        
        red_dominant = np.sum((red_channel > green_channel) & (red_channel > blue_channel))
        total_pixels = img_array.shape[0] * img_array.shape[1]
        red_ratio = red_dominant / total_pixels
        
        pink_mask = (
            (red_channel > 150) & (red_channel < 255) &
            (green_channel > 80) & (green_channel < 200) &
            (blue_channel > 80) & (blue_channel < 200) &
            (red_channel > green_channel) & (red_channel > blue_channel)
        )
        pink_ratio = np.sum(pink_mask) / total_pixels
        
        red_pink_mask = (
            ((red_channel > 180) & (green_channel < 150) & (blue_channel < 150)) |
            ((red_channel > 150) & (red_channel < 230) & 
             (green_channel > 100) & (green_channel < 180) &
             (blue_channel > 100) & (blue_channel < 180))
        )
        tongue_color_ratio = np.sum(red_pink_mask) / total_pixels
        
        brightness = np.mean(img_array)
        
        is_tongue = False
        confidence = 0
        reasons = []
        
        if tongue_color_ratio > 0.15:
            is_tongue = True
            confidence += 40
            reasons.append('检测到舌体颜色特征')
        
        if pink_ratio > 0.1:
            is_tongue = True
            confidence += 30
            reasons.append('检测到粉红色区域')
        
        if red_ratio > 0.3:
            confidence += 20
            reasons.append('红色通道占主导')
        
        if 100 < brightness < 200:
            confidence += 10
            reasons.append('亮度适中')
        
        if confidence >= 50:
            is_tongue = True
        
        return jsonify({
            'success': True,
            'is_tongue': is_tongue,
            'confidence': min(confidence, 100),
            'reasons': reasons,
            'message': '图片验证通过' if is_tongue else '未检测到舌象特征，请上传清晰的舌头照片'
        })
        
    except Exception as e:
        print(f"舌象验证错误: {e}")
        return jsonify({
            'success': False, 
            'message': f'图片验证失败: {str(e)}', 
            'is_tongue': False
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({'status': 'ok', 'timestamp': datetime.now().isoformat()})

# ==================== 诊断趋势数据 API ====================

@app.route('/api/diagnosis/clear', methods=['DELETE'])
@login_required
def clear_diagnosis_history():
    """清除用户诊断历史记录"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'message': '数据库连接失败'}), 500
        
        cursor = conn.cursor()
        cursor.execute("DELETE FROM DiagnosisRecords WHERE UserId = ?", (session['user_id'],))
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': '诊断记录已清空'})
    
    except Exception as e:
        print(f"清除诊断记录错误: {e}")
        return jsonify({'success': False, 'message': f'清除失败: {str(e)}'}), 500

@app.route('/api/diagnosis/trend', methods=['GET'])
@login_required
def get_diagnosis_trend():
    """获取用户诊断趋势数据"""
    try:
        records = get_user_diagnosis_history(session['user_id'])
        
        trend_data = {
            'heyi': [],
            'xila': [],
            'badagan': [],
            'labels': []
        }
        
        for record in records:
            try:
                result = json.loads(record['Result'])
            except:
                result = {}
            
            constitution = result.get('constitution', '')
            symptoms = result.get('symptoms', [])
            date = record['CreatedAt']
            
            trend_data['labels'].append(date.strftime('%m-%d %H:%M'))
            
            heyi_val = 50
            xila_val = 50
            badagan_val = 50
            
            if '赫依' in constitution:
                heyi_val = 65 + (symptoms.count('心慌') + symptoms.count('失眠') + symptoms.count('手脚麻')) * 5
                xila_val = 45
                badagan_val = 50
            elif '希拉' in constitution:
                heyi_val = 45
                xila_val = 65 + (symptoms.count('口干') + symptoms.count('口苦') + symptoms.count('心烦')) * 5
                badagan_val = 45
            elif '巴达干' in constitution:
                heyi_val = 45
                xila_val = 45
                badagan_val = 65 + (symptoms.count('怕冷') + symptoms.count('腹胀') + symptoms.count('痰多')) * 5
            
            trend_data['heyi'].append(min(max(heyi_val, 30), 90))
            trend_data['xila'].append(min(max(xila_val, 30), 90))
            trend_data['badagan'].append(min(max(badagan_val, 30), 90))
        
        trend_data['labels'].reverse()
        trend_data['heyi'].reverse()
        trend_data['xila'].reverse()
        trend_data['badagan'].reverse()
        
        return jsonify({'success': True, 'trend': trend_data})
    
    except Exception as e:
        print(f"获取趋势数据错误: {e}")
        return jsonify({'success': False, 'message': f'获取失败: {str(e)}'}), 500

# ==================== 知识图谱 API ====================

@app.route('/api/knowledge/graph/roots', methods=['GET'])
def get_three_roots():
    """获取三根信息"""
    try:
        graph = get_knowledge_graph()
        # 这里可以扩展为从数据库获取三根信息
        roots = [
            {"name": "赫依", "description": "气，主导精神活动和生命机能"},
            {"name": "希拉", "description": "火，主导消化和代谢功能"},
            {"name": "巴达干", "description": "水和土，主导营养和生长功能"}
        ]
        return jsonify({'success': True, 'roots': roots})
    except Exception as e:
        print(f"获取三根信息错误: {e}")
        return jsonify({'success': False, 'message': f'获取失败: {str(e)}'}), 500

@app.route('/api/knowledge/graph/match', methods=['POST'])
def match_root_by_symptoms():
    """根据症状匹配根"""
    try:
        data = request.get_json()
        symptoms = data.get('symptoms', [])
        
        if not symptoms:
            return jsonify({'success': False, 'message': '症状列表不能为空'}), 400
        
        graph = get_knowledge_graph()
        result = graph.get_root_by_symptoms(symptoms)
        
        return jsonify({'success': True, 'matches': result})
    except Exception as e:
        print(f"匹配症状错误: {e}")
        return jsonify({'success': False, 'message': f'匹配失败: {str(e)}'}), 500

@app.route('/api/knowledge/graph/pulse/<root_name>', methods=['GET'])
def get_pulse_features(root_name):
    """获取根的脉象特征"""
    try:
        graph = get_knowledge_graph()
        result = graph.get_pulse_features_by_root(root_name)
        
        return jsonify({'success': True, 'features': result})
    except Exception as e:
        print(f"获取脉象特征错误: {e}")
        return jsonify({'success': False, 'message': f'获取失败: {str(e)}'}), 500

@app.route('/api/knowledge/graph/treatment/<root_name>', methods=['GET'])
def get_treatments(root_name):
    """获取根的调理方法"""
    try:
        graph = get_knowledge_graph()
        result = graph.get_treatments_by_root(root_name)
        
        return jsonify({'success': True, 'treatments': result})
    except Exception as e:
        print(f"获取调理方法错误: {e}")
        return jsonify({'success': False, 'message': f'获取失败: {str(e)}'}), 500

@app.route('/api/knowledge/graph/inference', methods=['POST'])
def get_inference_path():
    """获取症状到体质的推理路径"""
    try:
        data = request.get_json()
        symptoms = data.get('symptoms', [])
        
        if not symptoms:
            return jsonify({'success': False, 'message': '症状列表不能为空'}), 400
        
        graph = get_knowledge_graph()
        result = graph.get_inference_path(symptoms)
        
        return jsonify({'success': True, 'paths': result})
    except Exception as e:
        print(f"获取推理路径错误: {e}")
        return jsonify({'success': False, 'message': f'获取失败: {str(e)}'}), 500

@app.route('/api/knowledge/graph/data', methods=['GET'])
def get_graph_data():
    """获取知识图谱的节点和边数据"""
    try:
        graph = get_knowledge_graph()
        result = graph.get_graph_nodes_and_edges()
        
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        print(f"获取图谱数据错误: {e}")
        return jsonify({'success': False, 'message': f'获取失败: {str(e)}'}), 500

# ==================== LSTM健康趋势预测 API ====================

@app.route('/api/health/predict', methods=['POST'])
@login_required
def predict_health_trend():
    """使用LSTM+注意力机制预测未来健康趋势"""
    try:
        data = request.get_json()
        days = data.get('days', 30)  # 默认预测30天
        
        # 获取用户诊断历史
        records = get_user_diagnosis_history(session['user_id'])
        
        if len(records) < 3:
            return jsonify({
                'success': False,
                'message': f'需要至少3次历史诊断记录才能进行预测，当前有{len(records)}次记录',
                'records_count': len(records)
            }), 400
        
        # 准备历史数据
        history_data = []
        for record in records:
            history_data.append({
                'result': record['Result'],
                'created_at': record['CreatedAt'].isoformat() if record['CreatedAt'] else None
            })
        
        # 使用LSTM预测
        predictions = predict_future(history_data, days)
        
        # 生成健康预警
        warnings = generate_health_warnings(predictions)
        
        return jsonify({
            'success': True,
            'predictions': predictions,
            'warnings': warnings,
            'historical_data': prepare_historical_for_frontend(records),
            'model_used': 'LSTM+Attention' if len(records) >= 7 else 'Simulation'
        })
        
    except Exception as e:
        print(f"LSTM预测错误: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'预测失败: {str(e)}'
        }), 500

def generate_health_warnings(predictions):
    """根据预测结果生成健康预警"""
    warnings = []
    
    if not predictions or len(predictions) < 1:
        return warnings
    
    # 获取最后一个预测
    last_pred = predictions[-1]
    
    if last_pred['heyi'] > 75:
        warnings.append({
            'type': 'warning',
            'root': '赫依',
            'level': 'high',
            'message': '赫依值偏高，建议注意休息，避免过度劳累，保持情绪稳定',
            'advice': ['保证充足睡眠', '减少焦虑情绪', '适当进行轻度运动']
        })
    elif last_pred['heyi'] < 30:
        warnings.append({
            'type': 'warning',
            'root': '赫依',
            'level': 'medium',
            'message': '赫依值偏低，建议适当增加运动，保持气血通畅',
            'advice': ['适度运动', '保持规律作息', '饮食营养均衡']
        })
    
    if last_pred['xila'] > 75:
        warnings.append({
            'type': 'warning',
            'root': '希拉',
            'level': 'high',
            'message': '希拉值偏高，建议清淡饮食，避免辛辣刺激食物',
            'advice': ['多喝水', '避免辛辣食物', '保持情绪平和']
        })
    elif last_pred['xila'] < 30:
        warnings.append({
            'type': 'warning',
            'root': '希拉',
            'level': 'medium',
            'message': '希拉值偏低，建议适当补充温热食物',
            'advice': ['适当食用温性食物', '注意保暖', '适度运动']
        })
    
    if last_pred['badagan'] > 75:
        warnings.append({
            'type': 'warning',
            'root': '巴达干',
            'level': 'high',
            'message': '巴达干值偏高，建议加强运动，避免生冷食物',
            'advice': ['增加运动', '避免生冷饮食', '保持环境干燥']
        })
    elif last_pred['badagan'] < 30:
        warnings.append({
            'type': 'warning',
            'root': '巴达干',
            'level': 'medium',
            'message': '巴达干值偏低，建议营养饮食，保持充足睡眠',
            'advice': ['营养均衡饮食', '保证充足睡眠', '适当进补']
        })
    
    if len(warnings) == 0:
        warnings.append({
            'type': 'success',
            'root': 'all',
            'level': 'low',
            'message': '三根平衡状态良好，继续保持健康生活方式！',
            'advice': ['规律作息', '均衡饮食', '适度运动']
        })
    
    return warnings

def prepare_historical_for_frontend(records):
    """将历史记录转换为前端可用格式"""
    historical = []
    
    for record in records:
        try:
            result = json.loads(record.get('Result', '{}'))
            constitution = result.get('constitution', '')
            symptoms = result.get('symptoms', [])
            date = record.get('CreatedAt')
            
            # 计算三根值
            heyi_val = 50
            xila_val = 50
            badagan_val = 50
            
            if '赫依' in constitution:
                heyi_val = 65 + (symptoms.count('心慌') + symptoms.count('失眠') + symptoms.count('手脚麻')) * 5
                xila_val = 45
            elif '希拉' in constitution:
                xila_val = 65 + (symptoms.count('口干') + symptoms.count('口苦') + symptoms.count('心烦')) * 5
                heyi_val = 45
            elif '巴达干' in constitution:
                badagan_val = 65 + (symptoms.count('怕冷') + symptoms.count('腹胀') + symptoms.count('痰多')) * 5
                heyi_val = 45
            
            historical.append({
                'date': date.strftime('%m-%d %H:%M') if date else None,
                'heyi': min(max(heyi_val, 20), 95),
                'xila': min(max(xila_val, 20), 95),
                'badagan': min(max(badagan_val, 20), 95),
                'constitution': constitution
            })
        except Exception as e:
            continue
    
    return list(reversed(historical))  # 按时间正序排列

# ==================== 前端静态文件服务 ====================

@app.route('/')
def index():
    return send_from_directory('../frontend', 'index.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('../frontend', path)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)