# backend/db.py

import pyodbc
from config import config

def get_db_connection():
    """获取数据库连接"""
    try:
        conn = pyodbc.connect(config.DB_CONNECTION_STRING, timeout=30)
        return conn
    except Exception as e:
        print(f"数据库连接失败: {e}")
        raise

def execute_query(sql, params=None, fetch_one=False, fetch_all=False):
    """执行查询语句"""
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if params:
            cursor.execute(sql, params)
        else:
            cursor.execute(sql)
        
        if fetch_one:
            result = cursor.fetchone()
            return result
        elif fetch_all:
            result = cursor.fetchall()
            return result
        else:
            conn.commit()
            return cursor.rowcount
    except Exception as e:
        if conn:
            conn.rollback()
        raise e
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def execute_procedure(proc_name, params=None):
    """执行存储过程"""
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if params:
            cursor.execute(f"EXEC {proc_name} " + ",".join(["?"] * len(params)), params)
        else:
            cursor.execute(f"EXEC {proc_name}")
        
        # 获取结果
        results = []
        while True:
            if cursor.description:
                columns = [column[0] for column in cursor.description]
                rows = cursor.fetchall()
                for row in rows:
                    results.append(dict(zip(columns, row)))
            if not cursor.nextset():
                break
        
        conn.commit()
        return results
    except Exception as e:
        if conn:
            conn.rollback()
        raise e
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# 用户相关操作
def create_user(email, password_hash, name):
    """创建新用户"""
    sql = """
        INSERT INTO Users (Email, PasswordHash, Name)
        VALUES (?, ?, ?)
    """
    return execute_query(sql, (email, password_hash, name))

def get_user_by_email(email):
    """根据邮箱获取用户"""
    sql = "SELECT Id, Email, PasswordHash, Name, CreatedAt, LastLoginAt FROM Users WHERE Email = ?"
    return execute_query(sql, (email,), fetch_one=True)

def get_user_by_id(user_id):
    """根据ID获取用户"""
    sql = "SELECT Id, Email, Name, CreatedAt, LastLoginAt FROM Users WHERE Id = ?"
    return execute_query(sql, (user_id,), fetch_one=True)

def update_last_login(user_id):
    """更新最后登录时间"""
    sql = "UPDATE Users SET LastLoginAt = GETDATE() WHERE Id = ?"
    return execute_query(sql, (user_id,))

# 诊断记录相关操作
def save_diagnosis_record(user_id, result, advice):
    """保存诊断记录"""
    sql = """
        INSERT INTO DiagnosisRecords (UserId, Result, Advice, CreatedAt)
        VALUES (?, ?, ?, GETDATE())
    """
    return execute_query(sql, (user_id, result, advice))

def get_user_diagnosis_history(user_id):
    """获取用户诊断历史"""
    return execute_procedure('sp_GetUserDiagnosisHistory', (user_id,))

# 调理打卡相关操作
def check_today_regimen(user_id, today_date):
    """检查今日是否已打卡"""
    results = execute_procedure('sp_CheckTodayRegimen', (user_id, today_date))
    if results and len(results) > 0:
        return results[0].get('Count', 0) > 0
    return False

def add_regimen_record(user_id, record_date):
    """添加调理打卡记录"""
    results = execute_procedure('sp_AddRegimenRecord', (user_id, record_date))
    if results and len(results) > 0:
        return results[0].get('Id')
    return None

def get_regimen_records(user_id):
    """获取用户所有调理打卡记录"""
    sql = "SELECT Id, RecordDate, CreatedAt FROM RegimenRecords WHERE UserId = ? ORDER BY RecordDate DESC"
    return execute_query(sql, (user_id,), fetch_all=True)

def get_regimen_count_by_user(user_id):
    """获取用户打卡总数"""
    sql = "SELECT COUNT(1) AS Count FROM RegimenRecords WHERE UserId = ?"
    result = execute_query(sql, (user_id,), fetch_one=True)
    return result[0] if result else 0