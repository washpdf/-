backend 目录 - 后端服务
====================================================================

目录作用
--------
本目录包含项目的所有后端服务代码，负责API接口、数据处理、模型推理、数据库交互等核心功能。

文件说明
--------
核心服务文件：
├── app.py                    # Flask主应用，包含所有API路由
├── config.py                 # 应用配置文件（数据库连接等）
├── requirements.txt          # Python依赖包列表
├── package.json              # Node.js依赖配置（代理服务）
├── package-lock.json         # Node.js依赖锁定文件
└── proxy.js                  # 阿里云百炼API代理服务（Node.js）

核心功能模块：
├── knowledge_graph.py        # 蒙医知识图谱管理模块
├── lstm_prediction.py        # LSTM+注意力机制预测模块
├── neo4j_config.py           # Neo4j数据库配置
├── db.py                     # 数据库操作模块
└── mengyi_diagnosis_service.py # 蒙医诊断服务模块

缓存目录：
└── __pycache__/              # Python字节码缓存目录

主要API接口
------------
用户认证：
- POST /api/auth/register     # 用户注册
- POST /api/auth/login        # 用户登录
- POST /api/auth/logout       # 用户登出
- GET  /api/auth/session      # 获取当前会话

诊断功能：
- POST /api/tongue/validate   # 舌象验证
- POST /api/diagnosis/save    # 保存诊断记录
- GET  /api/diagnosis/history # 获取诊断历史
- GET  /api/diagnosis/trend   # 获取诊断趋势

调理功能：
- GET  /api/regimen/check     # 检查今日打卡
- POST /api/regimen/record    # 添加打卡记录

知识图谱：
- GET  /api/knowledge/graph/roots      # 获取三根信息
- POST /api/knowledge/graph/match      # 根据症状匹配根
- GET  /api/knowledge/graph/pulse/{root} # 获取脉象特征
- GET  /api/knowledge/graph/treatment/{root} # 获取调理方法
- POST /api/knowledge/graph/inference  # 获取推理路径
- GET  /api/knowledge/graph/data       # 获取图谱数据

健康预测：
- POST /api/health/predict    # LSTM健康趋势预测

环境配置
--------
1. Python环境：安装 requirements.txt 中的依赖
2. 数据库：SQL Server + Neo4j
3. Node.js：运行 proxy.js 需要Node.js环境
4. 环境变量：ALIYUN_API_KEY（阿里云API密钥）

启动方式
--------
Python后端：
    python app.py

代理服务（新开终端）：
    cd backend
    node proxy.js
