# DistillAI

> 将人类的智慧蒸馏进 AI Agent — 打造永不疲倦的数字分身
> Distill human wisdom into AI Agents — create tireless digital twins

**MIT License | 26+ Personas | CCv3 Compatible | i18n (中文/EN/JP)**

---

## 🎯 核心特性 | Core Features

- **有情感的 Agent 系统** — 不是冰冷机械的问答机器人，而是有性格、有记忆、能使用工具的 AI 分身
- **情绪检测** — 自动检测用户情绪（positive/negative/neutral），带情感化回应
- **Anti-LLM 偏见修正** — edge_cases + catchphrases 强制人格有棱角，不生成"安全无聊"回复
- **工具系统** — 自动匹配合适的工具（股票/天气/计算/新闻等）
- **记忆持久化** — 跨 session 记住重要上下文
- **分身系统** — 分裂/合并/分享人格，市场交易
- **多模型支持** — MiniMax / OpenAI / Anthropic / Ollama 本地大模型
- **多语言SDK** — Python / JavaScript / Go / Rust / Java / C# 客户端
- **多语言界面** — 中文 / English / 日本語 界面

---

## 🚀 快速开始 | Quick Start

### Python

```python
from distill import Distiller
d = Distiller()

# 简单聊天 | Simple chat
d.chat('巴菲特', '茅台值得买吗？')
# -> 回复: "茅台是好公司，但要看价格..."

# 创建有情感的 Agent
agent = d.create_spawn('巴菲特')
result = agent.run('茅台现在多少钱？', user_id='主人')
print(result['reply'])       # AI回复
print(result['emotion'])     # 用户情绪
print(result['tools_used'])  # 使用的工具

# 多视角对比
d.compare(['巴菲特', '禅师'], '50万怎么投资？')

# 克隆分身
d.clone_persona('巴菲特', '价值投资者')

# 分裂合并
d.merge_personas('巴菲特', '禅师', '投资禅师')

# 生成分身链接
link = d.share_persona('沙雕网友')
```

### CLI

```bash
cd distill-ai
python -m distill.cli ask 巴菲特 "茅台值得买吗？"
python -m distill.cli debate 巴菲特 禅师 "现在该买股票吗？"
python -m distill.cli compare 巴菲特,禅师,沙雕网友 "50万怎么投资"
python -m distill.cli scenario 禅师 "用户焦虑怎么办？"
```

### Flask API 服务器

```bash
python distill/api/server.py
# 5000 - REST API
# 5001 - Webhook回调（飞书/Telegram/Discord）
# 文档: GET /docs
# 健康检查: GET /health
```

### Docker

```bash
docker build -t distill-ai .
docker run -p 5000:5000 -p 5001:5001 distill-ai
```

---

## 📦 预置人格 (26个) | Built-in Personas (26)

**商业/投资 | Business/Investment**: 巴菲特, 查理芒格, 索罗斯, 瑞·达利欧, 彼得林奇, 桥水达里奥, 朱啸虎, 区块链大师

**情感/限制级 | Emotional/NSFW**: 树洞姐姐, 禅师, 沙雕网友, 幽灵黑客, 知心姐姐

**创作/捏人 | Creative**: ありさ, 御天, 一之瀨千雪, 幽灵船长, 神秘博士, 疯狂科学家, 星际瘾君子, 赛博精神病

---

## 🔧 工具系统 | Tool System

| 工具 | 说明 |
|------|------|
| `stock_query` | 股票查询（腾讯行情API） |
| `get_weather` | 天气预报 |
| `calculate` | 数学计算 |
| `get_news` | 新闻获取 |
| `web_search` | 网页搜索 |
| `sentiment_analysis` | 情感分析 |
| `get_date` | 日期时间 |
| `unit_convert` | 单位换算 |

---

## 🌍 多语言支持 | Multi-Language Support

### API 多语言请求

```bash
curl http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -H "Accept-Language: zh-CN" \
  -d '{"persona":"巴菲特","message":"茅台"}'
```

### 多语言SDK

```python
# Python
from distill.clients.python import DistillAIClient
client = DistillAIClient(api_key="***", lang="zh-CN")

# JavaScript
const { DistillAI } = require('./clients/javascript.js')
const client = new DistillAI({ apiKey: '***', language: 'zh-CN' })

# Go
// 见 clients/go/distill.go

# Rust
// 见 clients/rust/distillai.rs

# Java
// 见 clients/java/DistillAIClient.java

# C#
// 见 clients/csharp/DistillAIClient.cs
```

### 界面语言

DistillAI 支持中文 / English / 日本語 界面切换，通过 `Accept-Language` header 或 SDK 语言参数控制。

---

## 🏗️ 项目架构 | Architecture

```
distill-ai/
├── distill/
│   ├── __init__.py          # Distiller 入口
│   ├── agent.py             # Agent 运行时
│   ├── providers/           # 模型提供商 (MiniMax/OpenAI/Ollama)
│   ├── tools/               # 内置工具 (9个)
│   ├── tools_extended.py    # 扩展工具
│   ├── persona_skills.py    # 44个人格专属技能
│   ├── memory_v2.py         # Mem0风格语义记忆
│   ├── memory_vector.py     # FAISS向量搜索 ⭐NEW
│   ├── memory_sqlite.py      # SQLite后端
│   ├── security.py          # API认证、速率限制、内容过滤
│   ├── personas/             # 26个预置人格
│   ├── presets.py           # 预设
│   ├── presets_extended.py  # 扩展预设
│   ├── en_personas.py       # 英文人格
│   ├── personas_extra.py    # 额外人格
│   ├── spawn.py             # 分身系统
│   └── api/
│       └── server.py        # Flask REST API ⭐SECURED v2.5
├── clients/                 # 多语言SDK
│   ├── python.py
│   ├── javascript.js
│   ├── go/distill.go
│   ├── java/DistillAIClient.java
│   ├── rust/distillai.rs
│   └── csharp/DistillAIClient.cs
├── wechat_distiller.py      # 微信聊天 → 人格蒸馏
├── universal_distiller.py  # 通用输入源解析 (14种)
├── voice_distiller.py       # 语音 → 人格蒸馏
├── distill_self_check.py    # 自检脚本
└── stock_report.py         # 股票报告生成
```

---

## 📡 API 端点 | API Endpoints

| 端点 | 方法 | 说明 |
|------|------|------|
| `/health` | GET | 健康检查 |
| `/docs` | GET | API文档 |
| `/api/chat` | POST | 简单聊天 |
| `/api/agent/chat` | POST | 完整Agent聊天 |
| `/api/personas` | GET | 列出所有人格 |
| `/api/clone` | POST | 克隆人格 |
| `/api/share/<name>` | GET | 生成分身链接 |
| `/api/memory/<name>` | GET/POST | 记忆管理 |
| `/api/ccv3/<name>` | GET | 导出CCv3格式 |
| `/api/debate` | POST | 双人格辩论 |
| `/api/key` | GET/POST | API Key管理 |
| `/api/key/generate-default` | GET | 生成默认Key |

> 所有端点需要 Bearer token 认证 (除 `/health` 和 `/docs`)

---

## 🎭 人格蒸馏 | Persona Distillation

### 从聊天记录蒸馏

```python
from wechat_distiller import WeChatParser, PersonaDistiller, PersonaCardGenerator
parser = WeChatParser()
parser.load_txt("chat.txt")
analysis = PersonaDistiller().analyze(parser.messages, target_sender="张三")
persona = PersonaCardGenerator().generate(analysis, name="张三")
```

### 从语音蒸馏

```python
from voice_distiller import VoiceDistiller
vd = VoiceDistiller()
report = vd.distill("voice_message.mp3")
audio = vd.speak("Hello from your voice persona", voice_config=report)
```

### 通用来源蒸馏

```python
from universal_distiller import UniversalParser
parser = UniversalParser()
# 支持: WeChat/QQ/Telegram/Discord/WhatsApp/Slack/Signal/Email/Books/Twitter/RSS/Forums/Notes
parser.load("source_file", source_type="wechat")
persona = parser.distill(name="My Persona")
```

---

## 📚 支持的输入源 (14种) | Supported Sources (14)

WeChat (微信) | QQ | Telegram | Discord | WhatsApp | Slack | Signal | Email | Books | Twitter | RSS | Forums | Notes | Custom text

---

## 🔐 安全 | Security

API Key 认证 (Bearer token) | 速率限制 (Key/IP级别) | 内容过滤 | 越狱检测 | 角色权限 (read/write/admin)

详见 [SECURITY.md](SECURITY.md)

---

## 📄 许可证 | License

MIT License — 详见 [LICENSE](LICENSE)

---

## 🤝 贡献 | Contributing

欢迎贡献！详见 [CONTRIBUTING.md](CONTRIBUTING.md)