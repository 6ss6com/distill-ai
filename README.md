# DistillAI — 将人类的智慧蒸馏进 AI Agent

> **让每个人都能创建永不疲倦的数字分身**
> 将聊天记录、语音、文档变成有灵魂的 AI 人格，7行代码跑起来。

[![DistillAI](https://img.shields.io/badge/version-v2.6-blue.svg?style=flat-square)](https://github.com/6ss6com/distill-ai)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg?style=flat-square)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-blue.svg?style=flat-square)](https://www.python.org/downloads/)
[![CCv3 Compatible](https://img.shields.io/badge/CCv3-Compatible-ff69b4.svg?style=flat-square)](https://github.com/microsoft/character-card-format)

---

## ⭐ 一句话说明

**DistillAI** 是一个人格蒸馏平台 — 把微信聊天、语音、文档变成专属 AI 分身，让 AI 有性格、有记忆、能用工具。

---

## 🚀 3分钟快跑（小白专用）

### 第一步：安装

```bash
# 方法1：克隆（推荐）
git clone https://github.com/6ss6com/distill-ai.git
cd distill-ai

# 方法2：下载zip（不会用git用这个）
# 点右上角绿色 "Code" -> Download ZIP -> 解压到任意目录
```

### 第二步：运行（不需要安装！）

```bash
# Windows
python distill/api/server.py

# Mac/Linux
python3 distill/api/server.py
```

> ⚠️ 如果提示 `No module named 'flask'`：先运行 `pip install flask requests`  
> 或者用： `python -m pip install flask flask-cors` 如果报错看 [常见问题](#-常见问题)

### 第三步：打开使用

浏览器打开 → http://localhost:5000/docs

看到 Swagger 界面就成功了！点击任意接口右侧 "Try it out" 就能用。

---

## 🎯 功能一览

| 功能 | 说明 |
|------|------|
| 🤖 **26个人格** | 巴菲特/禅师/沙雕网友等，开箱即用 |
| 💬 **聊天** | `d.chat('巴菲特', '茅台值得买吗？')` |
| 🔍 **向量记忆** | 跨session记住重要信息，语义搜索 |
| 🛡️ **安全API** | Bearer token认证，速率限制，内容过滤 |
| 📡 **HTTP API** | REST接口，支持飞书/Discord/Telegram |
| 🔢 **CCv3导出** | 一键导出角色卡，导入SillyTavern |
| 🌐 **多语言** | 中文/English/日本語界面 |
| 📦 **多语言SDK** | Python / JavaScript / Go / Rust / Java / C# |
| 🧠 **Anti-LLM偏见** | edge_cases + catchphrases 让人格有棱角 |
| 🔊 **语音蒸馏** | 微信语音/录音 → AI人格 |

---

## 📦 环境要求

| 项目 | 要求 |
|------|------|
| Python | 3.8+（推荐 3.11） |
| 内存 | 最少 2GB |
| 网络 | 需要访问 api.minimax.chat（国内可能需要代理） |
| 可选 | OpenAI API Key（如果没有，用MiniMax免费额度） |

---

## 🔧 详细安装（针对不同情况）

### 情况A：已有Python环境

```bash
cd distill-ai
pip install flask requests

# 启动API服务器
python distill/api/server.py
```

### 情况B：没有Python

1. 打开 https://www.python.org/downloads/
2. 下载 Python 3.11（认准 Windows installer）
3. 安装时 **✅ 勾选 "Add Python to PATH"**
4. 打开命令行，运行：
```bash
pip install flask requests
cd 你的distill-ai目录
python distill/api/server.py
```

### 情况C：conda环境

```bash
conda create -n distillai python=3.11
conda activate distillai
pip install flask requests
python distill/api/server.py
```

### 情况D：Docker（不需要Python）

```bash
# 构建镜像
docker build -t distill-ai .

# 运行
docker run -p 5000:5000 -p 5001:5001 distill-ai
```

> 访问 http://localhost:5000/docs

---

## 💡 快速使用示例

### Python SDK（最简单）

```python
from distill import Distiller

# 创建蒸馏器
d = Distiller()

# 1. 直接聊天（3行代码）
reply = d.chat('沙雕网友', '今天心情不好')
print(reply)

# 2. 有情感地聊天
reply = d.chat('巴菲特', '亏了好多万...', emotion='negative')
print(reply)

# 3. 对比两个人格
results = d.compare(['巴菲特', '禅师'], '50万怎么投资')
for name, reply in results.items():
    print(f"{name}: {reply}")

# 4. 两人辩论
result = d.debate('巴菲特', '禅师', '现在该买股票吗？')
print(result['opening'])   # 巴菲特开场
print(result['rebuttal'])  # 禅师反驳

# 5. 创建分身
agent = d.create_spawn('巴菲特')
result = agent.run('茅台现在多少钱？', user_id='主人')
print(result['reply'])

# 6. 克隆人格
d.clone_persona('巴菲特', '我的价值投资分身')

# 7. 合并人格
d.merge_personas('巴菲特', '禅师', '投资禅师')

# 8. 生成分身链接
link = d.share_persona('沙雕网友')
print(f"分享链接: {link}")
```

### CLI 命令行

```bash
# 进入目录
cd distill-ai

# 简单聊天
python -m distill.cli ask 巴菲特 "茅台值得买吗？"

# 辩论
python -m distill.cli debate 巴菲特 禅师 "现在该买股票吗？"

# 多视角对比
python -m distill.cli compare 巴菲特,禅师,沙雕网友 "50万怎么投资"

# 场景模拟
python -m distill.cli scenario 禅师 "用户焦虑怎么办？"
```

### HTTP API（需要启动服务器）

**启动服务器：**
```bash
python distill/api/server.py
```

**生成 API Key（首次）：**
```bash
# 浏览器打开 http://localhost:5000/api/key/generate-default
# 会返回一个类似这样的key:
# distill_xxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**聊天：**
```bash
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer 你的API密钥" \
  -d '{"persona":"巴菲特","message":"茅台值得买吗？"}'
```

**查看所有人格：**
```bash
curl http://localhost:5000/api/personas \
  -H "Authorization: Bearer 你的API密钥"
```

**CCv3导出（用于SillyTavern）：**
```bash
curl http://localhost:5000/api/ccv3/巴菲特 \
  -H "Authorization: Bearer 你的API密钥" \
  > buffett_ccv3.json

# 然后在 SillyTavern 中导入 buffett_ccv3.json
```

---

## 📡 API 完整文档

> 浏览器打开 http://localhost:5000/docs 查看交互式Swagger界面

### 认证

所有接口（除 `/health` 和 `/docs`）都需要 header：
```
Authorization: Bearer 你的API密钥
```

### 端点列表

| 端点 | 方法 | 说明 | 权限 |
|------|------|------|------|
| `/health` | GET | 健康检查 | 无需认证 |
| `/docs` | GET | API文档 | 无需认证 |
| `/api/chat` | POST | 简单聊天 | read |
| `/api/agent/chat` | POST | 完整Agent聊天 | read |
| `/api/personas` | GET | 列出所有人格 | read |
| `/api/personas/<name>` | GET | 获取单个人格 | read |
| `/api/clone` | POST | 克隆人格 | write |
| `/api/merge` | POST | 合并人格 | write |
| `/api/share/<name>` | GET | 生成分享链接 | read |
| `/api/memory/<name>` | GET | 获取记忆 | read |
| `/api/memory/<name>` | POST | 添加记忆 | write |
| `/api/ccv3/<name>` | GET | 导出CCv3角色卡 | read |
| `/api/debate` | POST | 双人格辩论 | read |
| `/api/compare` | POST | 多视角对比 | read |
| `/api/key` | GET | 列出所有Key | admin |
| `/api/key` | POST | 创建新Key | admin |
| `/api/key/<id>` | DELETE | 撤销Key | admin |

### 请求示例

**Agent聊天（带工具+情感）：**
```bash
curl -X POST http://localhost:5000/api/agent/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer 你的密钥" \
  -d '{
    "persona": "巴菲特",
    "message": "茅台现在多少钱？",
    "user_id": "主人"
  }'
```

**响应示例：**
```json
{
  "reply": "茅台是好公司，但要看看现在的价格..."
}
```

**添加记忆：**
```bash
curl -X POST http://localhost:5000/api/memory/巴菲特 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer 你的密钥" \
  -d '{
    "content": "用户主要投资A股，喜欢茅台和比亚迪",
    "importance": 3
  }'
```

---

## 🗂️ 内置人格（26个）

### 商业/投资
| 人格 | 描述 |
|------|------|
| 🧙‍♂️ **巴菲特** | 价值投资大师，稳健、长期主义 |
| 📈 **查理芒格** | 多元思维模型，逆向思考 |
| 🎯 **索罗斯** | 反身性理论，宏观交易 |
| 🏛️ **瑞·达利欧** | 风险平价，全天候策略 |
| 📊 **彼得林奇** | 成长股投资，善于发现tenbagger |
| 🏦 **区块链大师** | Crypto、Web3、DeFi |

### 情感/聊天
| 人格 | 描述 |
|------|------|
| 🌳 **树洞姐姐** | 温暖倾听，情感支持 |
| 🧘 **禅师** | 冥想引导，心灵开导 |
| 😂 **沙雕网友** | 搞笑幽默，吐槽之王 |
| 👻 **幽灵黑客** | 神秘技术宅，说话带黑话 |
| 💕 **知心姐姐** | 知性温柔，感情建议 |

### 创作/角色
| 人格 | 描述 |
|------|------|
| 👩 **ありさ** | 活泼可爱，日系偶像 |
| ⚔️ **御天** | 武侠剑客，江湖气息 |
| ❄️ **一之濑千雪** | 冷傲高冷，冰雪美人 |
| 🚢 **幽灵船长** | 海盗船长，粗犷豪放 |
| 🧪 **疯狂科学家** | 科学怪人，发明家 |
| 🌌 **星际瘾君子** | 赛博朋克，迷幻风格 |

---

## 🧠 记忆系统详解

DistillAI 有三层记忆：

### 1. 对话记忆（内置，自动）
每个session的对话自动存储，Agent能记住上一轮说了什么。

### 2. 语义记忆（向量搜索）
```python
# 添加重要记忆
vm = VectorMemory('巴菲特')
vm.add('用户主要投资A股，最关注茅台和比亚迪', {
    'importance': 3,
    'tags': ['投资', 'A股']
})

# 语义搜索
results = vm.search('我的投资偏好是什么？', k=3)
for r in results:
    print(f"[{r['relevance_score']:.2f}] {r['content']}")

# 获取相关上下文（用于注入LLM）
context = vm.get_relevant('投资建议', k=5)
```

### 3. 持久化记忆（SQLite）
自动保存，跨session不丢失。

---

## 🔧 配置说明

### 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `MINIMAX_API_KEY` | MiniMax API密钥 | 无（必须设置） |
| `OPENAI_API_KEY` | OpenAI备用密钥 | 无 |
| `LLM_BASE_URL` | LLM API地址 | https://api.minimax.chat/v1 |
| `COMFYUI_HOST` | ComfyUI地址 | localhost |
| `COMFYUI_PORT` | ComfyUI端口 | 8188 |

### 获取MiniMax API Key

1. 打开 https://www.minimax.chat/
2. 注册账号（可用手机号）
3. 进入控制台 → API Key → 创建新Key
4. 复制 Key，设置为环境变量：

**Windows (PowerShell):**
```powershell
$env:MINIMAX_API_KEY = "你的密钥"
```

**Mac/Linux:**
```bash
export MINIMAX_API_KEY="你的密钥"
```

**Python代码中设置：**
```python
import os
os.environ['MINIMAX_API_KEY'] = '你的密钥'
```

---

## 🔐 安全设置

### 启动时不认证（本地开发）
```bash
python distill/api/server.py --no-auth
```

### 禁用速率限制（本地开发）
```bash
python distill/api/server.py --no-rate-limit
```

### 生成新的API Key（admin）
```bash
# 通过API
curl http://localhost:5000/api/key \
  -H "Authorization: Bearer 你的密钥" \
  -H "Content-Type: application/json" \
  -d '{"name":"我的应用","role":"read","expires_days":365}'
```

---

## 🐛 常见问题

### Q: 启动报错 `No module named 'flask'`
**原因：** 没有安装依赖  
**解决：**
```bash
pip install flask requests
```

### Q: 启动报错 `MINIMAX_API_KEY` not found
**原因：** 没有设置API密钥  
**解决：**
```bash
export MINIMAX_API_KEY="你的密钥"  # Mac/Linux
# 或在Python里:
import os
os.environ['MINIMAX_API_KEY'] = '你的密钥'
```

### Q: 聊天返回 `[Error] No LLM client configured`
**原因：** 同上，API密钥未设置  
**解决：** 设置 `MINIMAX_API_KEY` 环境变量

### Q: 浏览器打开 http://localhost:5000 显示 "This site can't be reached"
**原因：** 服务器没有启动，或端口不对  
**解决：**
1. 确认服务器在运行（命令行有输出）
2. 检查端口是否正确（默认5000）
3. 试试 http://127.0.0.1:5000

### Q: API返回 401 Unauthorized
**原因：** 没有带API Key或Key无效  
**解决：**
```bash
# 生成默认key
curl http://localhost:5000/api/key/generate-default

# 使用key访问
curl http://localhost:5000/api/personas \
  -H "Authorization: Bearer 你的密钥"
```

### Q: 速率限制 429
**原因：** 请求太频繁  
**解决：** 减慢请求频率，或申请更高额度

### Q: 回复质量不好
**原因：** API Key额度用完或网络问题  
**解决：** 检查MINIMAX_API_KEY是否有效，或换OpenAI Key

### Q: 如何查看所有可用人格？
```bash
curl http://localhost:5000/api/personas \
  -H "Authorization: Bearer 你的密钥"
```

### Q: 如何导出角色到SillyTavern？
```bash
curl http://localhost:5000/api/ccv3/巴菲特 \
  -H "Authorization: Bearer 你的密钥" \
  > buffett.json

# SillyTavern: Settings → Characters → Import → 选择buffett.json
```

### Q: 如何让AI记住更多信息？
```python
from distill.memory_vector import VectorMemory
vm = VectorMemory('巴菲特')
vm.add('用户是我朋友，推荐股票要谨慎', {'importance': 5})
```

### Q: Docker启动失败
**原因：** 可能端口被占用  
**解决：**
```bash
# 改端口
docker run -p 5001:5000 distill-ai
```

---

## 🏗️ 项目架构

```
distill-ai/
├── distill/
│   ├── __init__.py          # Distiller入口，26个人格
│   ├── agent.py             # Agent运行时（有情感的任务执行者）
│   ├── providers/            # 多模型支持（MiniMax/OpenAI/Ollama）
│   ├── tools/                # 内置工具（股票/天气/搜索等）
│   ├── persona_skills.py    # 44个人格专属技能
│   ├── memory_v2.py          # Mem0风格语义记忆
│   ├── memory_vector.py      # FAISS向量搜索 ⭐
│   ├── memory_sqlite.py      # SQLite持久化
│   ├── security.py           # API认证/速率限制/内容过滤
│   ├── spawn.py              # 分身系统（克隆/合并/分享）
│   └── api/
│       └── server.py         # Flask API（安全+文档）
├── clients/                  # 多语言SDK
│   ├── python.py            # Python客户端
│   ├── javascript.js        # JavaScript客户端
│   ├── go/distill.go        # Go客户端
│   ├── java/...             # Java客户端
│   ├── rust/...             # Rust客户端
│   └── csharp/...           # C#客户端
├── wechat_distiller.py       # 微信聊天→人格蒸馏
├── universal_distiller.py    # 通用输入源蒸馏（14种）
├── voice_distiller.py        # 语音→人格蒸馏
├── CLI.py                   # 命令行工具
└── README.md                # 本文档
```

---

## 🔢 多语言SDK

### Python
```python
from distill.clients.python import DistillAIClient
client = DistillAIClient(api_key="你的密钥", lang="zh-CN")
reply = client.chat("巴菲特", "茅台值得买吗？")
```

### JavaScript
```javascript
const { DistillAI } = require('./clients/javascript.js')
const client = new DistillAI({ apiKey: '你的密钥', language: 'zh-CN' })
const reply = await client.chat('巴菲特', '茅台值得买吗？')
```

### Go
```go
import "distill-ai/clients/go"
client := distill.NewClient("你的密钥")
reply, _ := client.Chat("巴菲特", "茅台值得买吗？")
```

---

## 🎭 从聊天记录创建人格

### 微信聊天记录

```python
from wechat_distiller import WeChatParser, PersonaDistiller, PersonaCardGenerator

# 1. 解析聊天记录
parser = WeChatParser()
parser.load_txt("chat.txt")  # 你的微信聊天记录导出文件

# 2. 分析人格
analysis = PersonaDistiller().analyze(
    parser.messages,
    target_sender="张三"  # 要蒸馏的人物名字
)

# 3. 生成角色卡
card = PersonaCardGenerator().generate(analysis, name="张三")

# 4. 保存
card.save("张三.json")
print(f"角色卡已生成：{card.name}")
```

### 语音文件

```python
from voice_distiller import VoiceDistiller

vd = VoiceDistiller()

# 从语音蒸馏人格
report = vd.distill("voice_message.mp3")

# 用这个声音说话
audio = vd.speak("你好，我是你的AI分身", voice_config=report)
```

### 通用来源（14种）

支持：微信/QQ/Telegram/Discord/WhatsApp/Slack/Signal/邮件/书籍/Twitter/RSS/论坛/笔记/自定义文本

```python
from universal_distiller import UniversalParser

parser = UniversalParser()
parser.load("chat.log", source_type="telegram")  # 指定来源类型
persona = parser.distill(name="我的Telegram人格")
```

---

## ⚡ 性能优化建议

| 场景 | 建议 |
|------|------|
| 响应慢 | 使用本地Ollama模型代替云API |
| 内存不足 | 减少history深度，减少向量维度 |
| 启动慢 | 预热LLM连接，首次请求会慢 |
| 高并发 | 使用Docker多容器部署 |

---

## 🆘 故障排查

| 问题 | 解决 |
|------|------|
| 一直报 `API key` 错误 | 重启终端，环境变量可能没生效 |
| 聊天回复空 | 检查MINIMAX_API_KEY是否有效 |
| 向量搜索没结果 | 检查vector_memory目录是否有权限 |
| Docker端口冲突 | `docker ps` 查看端口占用 |

### 获取详细日志

```bash
# 启动时加 --debug
python distill/api/server.py --debug

# 查看Python错误
python -c "from distill import Distiller; d = Distiller(); print(d.chat('巴菲特','hi'))"
```

---

## 📄 许可证

MIT License — 可自由使用、修改、商业化。

详见 [LICENSE](LICENSE)

---

## 🤝 贡献

欢迎提交Issue和Pull Request！  
详见 [CONTRIBUTING.md](CONTRIBUTING.md)

---

## 📊 版本历史

| 版本 | 日期 | 主要变化 |
|------|------|---------|
| **v2.6** | 2026-05-08 | 完善README + 向量搜索 + 安全中间件 |
| v2.5.1 | 2026-05-08 | 修复中文embedding + Swagger文档 |
| v2.5 | 2026-05-07 | 语音蒸馏 + 安全层 + 26个人格 |
| v2.0 | 2026-05-02 | Mem0记忆 + CCv3导出 |

---

**有问题？** 提 [Issue](https://github.com/6ss6com/distill-ai/issues) 或查看 [SECURITY.md](SECURITY.md)