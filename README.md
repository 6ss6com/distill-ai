# DistillAI

> 把人的智慧蒸馏进 AI Agent — 打造永不疲倦的数字分身
> Distill human wisdom into AI Agents — create tireless digital twins

**MIT License | 26+ Personas | CCv3 Compatible | Agent System v1.0**

---

## 🇨🇳 中文说明

### 核心特性

- **有感情的 Agent 系统** — 不是冷冰冰的问答机器人，而是有棱角、有记忆、能使用工具的 AI 分身
- **情感感知** — 自动检测用户情绪（positive/negative/neutral），带对应风格回应
- **人格棱角** — edge_cases + catchphrases 强制人格不掉进"AI安全回复"
- **工具调用** — 自动匹配合适的工具（股票查询/天气/计算/新闻等）
- **记忆持续** — 跨 session 记住重要上下文
- **分身系统** — 克隆/分享/合并/市场，让人格可复制可传递
- **多模型支持** — MiniMax / OpenAI / Anthropic / Ollama 本地大模型

### 快速开始

```python
from distill import Distiller
d = Distiller()

# 简单聊天
d.chat('巴菲特', '最近AI很火该投资吗')

# 创建有感情的Agent
agent = d.create_spawn('巴菲特')
result = agent.run('茅台现在多少钱？', user_id='主人')
print(result['reply'])       # AI回复
print(result['emotion'])     # 用户情绪
print(result['tools_used'])  # 使用的工具

# 多视角对比
d.compare(['巴菲特', '禅师'], '50万闲钱怎么投')

# 分身克隆
d.clone_persona('巴菲特', '价值投资者')

# 分身合并
d.merge_personas('巴菲特', '禅师', '投资禅师')

# 生成分享链接
link = d.share_persona('沙雕网友')
```

### API 服务器

```bash
python distill/api/server.py
# 5000 - REST API
# 5001 - Webhook回调（飞书/Telegram/Discord）
```

### 预置人格 (26个)

**商业/投资**: 巴菲特📈, 沙雕网友😂, 幽灵黑客💀

**情感/陪伴**: 树洞姐姐🌳, 禅师🧘, 深夜食堂老板🍜

**创作/虚构**: 苍炎剑士⚔️, 银发法师🔮, 九尾灵狐🦊, 星际舰长🚀

---

## 🇺🇸 English

### Core Features

- **Emotional Agent System** — AI agents with personality, memory, and tool use
- **Emotion Detection** — auto-detect user sentiment (positive/negative/neutral)
- **Anti-LLM Bias** — edge_cases + catchphrases keep agents from being "safe and boring"
- **Tool System** — 9 built-in tools: stock query, weather, calc, news, web, sentiment, etc.
- **Persistent Memory** — cross-session memory for each persona
- **Spawn System** — clone/share/merge persona, local marketplace
- **Multi-Model** — MiniMax / OpenAI / Anthropic / Ollama (local LLM) ✅

### Quick Start

```python
from distill import Distiller
d = Distiller()

# Simple chat
d.chat('Buffett', 'Should I invest in AI stocks?')

# Create emotional agent
agent = d.create_spawn('巴菲特')
result = agent.run('How much is Moutai stock?', user_id='owner')
print(result['reply'])
print(result['emotion'])
print(result['tools_used'])

# Multi-persona comparison
d.compare(['巴菲特', '禅师'], 'How to invest 500k?')

# Clone & merge
d.clone_persona('巴菲特', 'ValueInvestor')
d.merge_personas('巴菲特', '禅师', 'InvestmentZenMaster')
```

### API Server

```bash
python distill/api/server.py
# Port 5000 - REST API
# Port 5001 - Webhooks (Feishu/Telegram/Discord)
```

### REST Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/chat` | Simple chat |
| POST | `/api/agent/chat` | Agent chat (with tools) |
| POST | `/api/clone` | Clone persona |
| POST | `/api/merge` | Merge personas |
| GET | `/api/share/<name>` | Generate share link |
| POST | `/api/import` | Import from share link |
| GET | `/api/memory/<name>` | Get memory |
| POST | `/api/memory/<name>` | Add memory |
| GET | `/api/personas` | List all personas |
| POST | `/api/compare` | Multi-persona comparison |
| POST | `/api/debate` | Two-persona debate |

### Webhook Endpoints

| Path | Platform |
|------|----------|
| POST `/webhook/feishu` | Feishu (Lark) events |
| POST `/webhook/feishu/receive` | Feishu message receive |
| POST `/webhook/telegram` | Telegram Bot |
| POST `/webhook/discord` | Discord Bot |
| POST `/webhook/generic` | Generic webhook |

### Personas (26)

| Category | Personas |
|----------|----------|
| Business/Investment | 巴菲特📈, 沙雕网友😂, 幽灵黑客💀 |
| Emotional/Companion | 树洞姐姐🌳, 禅师🧘, 深夜食堂老板🍜 |
| Creative/Fictional | 苍炎剑士⚔️, 银发法师🔮, 九尾灵狐🦊, 星际舰长🚀 |
| Detective/Historical | Sherlock Holmes🕵️, Ancient Philosopher🏛️ |

---

## 🛠️ Tool System

| Tool | Description | Personas |
|------|-------------|----------|
| `stock_query` | Stock price/changes | 巴菲特, 禅师, 沙雕网友 |
| `news_search` | Latest news | 沙雕网友, 巴菲特 |
| `calc` | Math calculation | 巴菲特 |
| `date_info` | Date/time | 沙雕网友, 禅师 |
| `weather` | Weather query | 沙雕网友, 树洞姐姐 |
| `web_page` | Web content summary | 幽灵黑客, 巴菲特 |
| `stock_news` | Stock news | 巴菲特, 禅师 |
| `random_choice` | Random decision | 沙雕网友, 禅师 |
| `sentiment_analysis` | Emotion detection | 树洞姐姐, 禅师, 深夜食堂老板 |

---

## 📚 研究参考 | References

| Project | Stars | Use |
|---------|-------|-----|
| [fount](https://github.com/steve02081504/fount) | 695 | Modular AI character runtime |
| [mem0ai/mem0](https://github.com/mem0ai/mem0) | 54k+ | Universal memory layer for AI |
| [character-card-spec-v3](https://github.com/kwaroran/character-card-spec-v3) | 91 | CCv3 character card standard |
| [cyber-figures](https://github.com/cyber-immortal/cyber-figures) | 25 | Chinese persona distillation |
| [st-stepped-thinking](https://github.com/cierru/st-stepped-thinking) | 154 | Chain-of-thought for characters |

---

## 🇯🇵 日本語

### 特徴

- **感情のあるAgent** — ご質問に答え、メモリとツールを使用できる人格AI
- **感情検出** — ユーザーの感情を自動検出
- **Anti-LLM原則** — edge_cases + catchphrasesで人格を安全に保つ
- **ツールシステム** — 9つの組み込みツール
- **メモリシステム** — セッション間のメモリ永続化
- **分身システム** — クローン/シェア/マージ/マーケットプレイス

### クイックスタート

```python
from distill import Distiller
d = Distiller()
result = d.chat('巴菲特', 'AI株に投資すべき？')
print(result)
```

---

## License

MIT License - 商用・改変自由的 / Commercial and modification friendly