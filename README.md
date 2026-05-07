# DistillAI

> 把人的智慧蒸馏进 AI Agent — 打造永不疲倦的数字分身

**MIT License 开源项目**

## 核心概念

**DistillAI** = 人格蒸馏框架，通过多轮对话、决策记录、风格分析，把真实人物的知识、风格、决策模式转化为 AI Agent。

任何人（历史人物、名人、专家、自己）都可以被蒸馏。

## 架构

```
输入数据
├── 对话记录 (聊天记录/访谈/演讲)
├── 决策记录 (交易/写作/日常)
├── 文字作品 (书籍/文章/社交媒体)
├── 性格测试 / MBTI
└── 背景知识 (Wikipedia/百科)
    ↓
蒸馏引擎 (LLM 分析)
├── 人格提取 (Persona Extract)
├── 风格分析 (Style Analysis)
├── 知识结构化 (Knowledge Graph)
├── 决策模式 (Decision Patterns)
└── 价值观映射 (Value Mapping)
    ↓
输出: AI Twin Agent
├── 对话能力 (Chat)
├── 决策建议 (Decision)
├── 风格模仿 (Style)
└── 记忆持续更新 (Evolving)
```

## 预置人格 (22个)

| 分类 | 人格 | 特点 |
|------|------|------|
| 科学家 | 爱因斯坦、居里夫人、特斯拉、达芬奇 | 好奇、颠覆性思考 |
| 哲学家 | 苏格拉底、尼采、王阳明、孔子 | 追问、思辨、东方智慧 |
| 军事战略 | 孙子、俾斯麦 | 战略大师 |
| 政治领袖 | 林肯 | 铁血、务实 |
| 艺术大师 | 宫崎骏、卓别林、莎士比亚、金庸 | 创作风格鲜明 |
| 商业投资 | 巴菲特 | 价值投资 |
| 文学 | 鲁迅 | 批判现实 |
| 侦探/虚构 | 福尔摩斯 | 逻辑推理 |
| 原创角色 | 时间领主、硅谷创业导师、禅师 | 虚构人格 |

## 快速开始

```bash
# 克隆项目
git clone https://github.com/Ceeon/distill-ai.git
cd distill-ai

# 安装依赖
pip install jqdatasdk

# 蒸馏你自己 (需要 MiniMax API Key)
python -c "
from distill import Distiller
d = Distiller()
jin = d.distill_from_workspace('你的名字')
print('蒸馏完成!')
"

# 与人格聊天
python -c "
from distill import Distiller
d = Distiller()
reply = d.chat('爱因斯坦', '你觉得人工智能会取代人类吗？')
print(reply)
"

# 列出所有人格
python -c "
from distill import Distiller
d = Distiller()
import os
for f in os.listdir('distill/personas'):
    if f.endswith('.json'):
        print(' -', f.replace('.json',''))
"
```

## 聚宽股票分析集成

```bash
# 配置聚宽账号
# 编辑 joinquant_api.py 填入:
# JQ_USERNAME = "你的手机号"
# JQ_PASSWORD = "你的密码"

# 跑完整分析
python joinquant_api.py

# 生成每日报告
python stock_report.py
```

## 项目结构

```
distill-ai/
├── README.md
├── LICENSE              (MIT)
├── .gitignore
├── distill/
│   ├── __init__.py     核心蒸馏引擎
│   ├── cli.py          命令行工具
│   ├── presets.py      预置人格 (商业/历史)
│   ├── presets_extended.py 预置人格扩展 (20+人格)
│   └── personas/       人格档案 (JSON)
├── joinquant_api.py    聚宽数据接口
└── stock_report.py     每日股票报告生成
```

## License

MIT — 随意使用、修改、商业化
