# backend/neo4j_config.py

"""
Neo4j 数据库配置
"""

# Neo4j 数据库连接配置
# 请根据实际情况修改这些配置
NEO4J_CONFIG = {
    "uri": "neo4j+s://ff0cba83.databases.neo4j.io",  # Aura提供的URI
    "user": "ff0cba83",
    "password": "yV6wkr7coGk_Xbc7GFbuWMXmibiVl_SObizHZhZilCY"  # Aura生成的密码
}

# 知识图谱初始化配置
KG_CONFIG = {
    "auto_init": False,  # 是否在应用启动时自动初始化知识图谱（数据已存在，设为False）
    "init_data": False  # 是否初始化基础数据
}

# 错误处理配置
ERROR_CONFIG = {
    "ignore_connection_errors": True  # 是否忽略连接错误（用于开发环境）
}