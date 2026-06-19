const express = require('express');
const cors = require('cors');
const fetch = require('node-fetch');

const app = express();
app.use(cors());
app.use(express.json());

// ==================== DeepSeek V4 配置 ====================
// 从环境变量读取配置
const DEEPSEEK_API_KEY = process.env.DEEPSEEK_API_KEY || "";
const DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions";
const MODEL_NAME = "deepseek-v4-flash";  // 或 deepseek-v4-pro

// ==================== 代理接口 ====================
app.post('/api/aliyun', async (req, res) => {
    try {
        if (!DEEPSEEK_API_KEY) {
            return res.status(500).json({ error: "DeepSeek API Key未配置" });
        }

        let messages;
        if (req.body.messages) {
            messages = req.body.messages;
        } else if (req.body.prompt) {
            messages = [
                {
                    role: "system",
                    content: "你是一位精通蒙医三根理论的资深健康顾问，擅长根据用户的体质辨证结果，提供温和、具体、可操作的饮食与生活调理建议。请使用Markdown格式输出，包含标题和列表。"
                },
                { role: "user", content: req.body.prompt }
            ];
        } else {
            throw new Error("缺少 prompt 或 messages 参数");
        }

        const response = await fetch(DEEPSEEK_API_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${DEEPSEEK_API_KEY}`
            },
            body: JSON.stringify({
                model: MODEL_NAME,
                messages: messages,
                temperature: 0.7,
                max_tokens: 2000
            })
        });

        if (!response.ok) {
            const errorText = await response.text();
            console.error('DeepSeek API错误:', response.status, errorText);
            return res.status(response.status).json({
                error: `API请求失败: ${response.status}`,
                details: errorText
            });
        }

        const data = await response.json();
        res.json(data);

    } catch (error) {
        console.error('代理服务器错误:', error);
        res.status(500).json({ error: error.message });
    }
});

// 健康检查接口
app.get('/health', (req, res) => {
    res.json({ status: 'ok', service: 'deepseek-proxy', hasApiKey: !!DEEPSEEK_API_KEY });
});

// 获取配置信息（仅健康检查）
app.get('/config', (req, res) => {
    res.json({
        status: 'ok',
        model: MODEL_NAME,
        hasApiKey: !!DEEPSEEK_API_KEY
    });
});

app.listen(3000, () => {
    console.log('========================================');
    console.log('✅ DeepSeek V4 代理已启动');
    console.log('📍 代理地址: http://localhost:3000/api/aliyun');
    console.log('🔧 健康检查: http://localhost:3000/health');
    console.log('📦 使用模型: ' + MODEL_NAME);
    console.log('🔑 API Key 已配置: ' + (DEEPSEEK_API_KEY ? '是' : '否'));
    console.log('========================================');
});