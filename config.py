# backend/config.py

import os

class Config:
    """应用配置"""
    
    # Flask
    SECRET_KEY = 'your-secret-key-change-in-production-2024'
    
    # SQL Server 配置 (请根据你的实际情况修改)
    DB_SERVER = 'localhost'  # 或 '127.0.0.1'
    DB_NAME = 'MongolianMedicineDB'
    DB_USERNAME = 'sa'
    DB_PASSWORD = '961129Aa!'
    DB_DRIVER = '{ODBC Driver 17 for SQL Server}'
    
    # 连接字符串
    DB_CONNECTION_STRING = f"DRIVER={DB_DRIVER};SERVER={DB_SERVER};DATABASE={DB_NAME};UID={DB_USERNAME};PWD={DB_PASSWORD}"
    
   

config = Config()