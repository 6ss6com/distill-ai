# DistillAI

> 把人的智慧蒸馏进 AI Agent — 打造永不疲倦的数字分身

**MIT License 开源项目 | 34+预置人格 | CCv3兼容 | Anti-LLM偏见修正**

---

## 核心概念

**DistillAI** = 人格蒸馏框架，把真实人物的知识、风格、决策模式、独特"棱角"转化为 AI Agent。

任何人（历史人物、名人、专家、自己）都可以被蒸馏。

---

## 核心特性 v0.3

### Anti-LLM 偏见修正
LLM 默认生成"安全的、礼貌的、正确但平庸"的回复。
DistillAI 通过 `edge_cases` + `catchphrases` 强制人格保持"棱角"：

```
edge_cases: 被质疑时如何亮棱角
catchphrases: 专属口头禅/金句
```

### CCv3 格式兼容
导出为 Character Card V3 格式（行业标准），可直接用于 SillyTavern、RisuAI 等平台。

### Thinking Mode
让角色在回答前先"思考"（chain-of-thought），增强回复真实感。

### 多语言支持
中文 / English / 日本語，自动检测语言。

---

## 预置人格 (34个)

### 历史人物/名人
| 分类 | 人格 | 特点 |
|------|------|------|
| 科学家 | 爱因斯坦、居里夫人、特斯拉、达芬奇 | 颠覆性思考 |
| 哲学家 | 苏格拉底、尼采、王阳明、孔子 | 追问、思辨 |
| 军事战略 | 孙子、俾斯麦 | 战略大师 |
| 商业投资 | 巴菲特 📈 | 价值投资，有棱角 |
| 文学 | 鲁迅、金庸、莎士比亚 | 批判现实/文学创作 |
| 艺术大师 | 宫崎骏、卓别林 | 创作风格 |
| 侦探/虚构 | 福尔摩斯 🕵️ | 逻辑推理 |

### 原创角色
| 分类 | 人格 | 特点 |
|------|------|------|
| 游戏/动漫风 | 苍炎剑士⚔️、银发法师🔮、幽灵黑客💀 | 沉浸式角色扮演 |
| 赛博/科幻 | 星际舰长🚀、Cyberpunk Hacker💻 | 未来感 |
| 治愈/日常 | 深夜食堂老板🍜、树洞姐姐🌳 | 温暖治愈 |
| 东方玄幻 | 青云剑仙🌙、九尾灵狐🦊 | 古风仙侠 |
| 神秘/暗黑 | 赏金死神🩸、命运占卜师🃏、Mystic Oracle🔮 | 神秘学 |
| 哲学/禅 | 禅师、Ancient Philosopher🏛️ | 深度思考 |

---

## 快速开始

```bash
# 安装
pip install jqdatasdk  # 可选，用于股票分析

# 列出所有人格
python distill/cli.py list

# 快速问答
python distill/cli.py ask 巴菲特 "茅台还能买吗"
python distill/cli.py ask Buffett "Is Moutai worth it?"

# 随机人格回答
python distill/cli.py random "人生的意义是什么"

# 辩论
python distill/cli.py debate 巴菲特 禅师 "要不要辞职创业"

# 蒸馏自己的数字分身
python distill/cli.py distill 我的导师 "一个严厉但关心学生的人"

# 多视角对比
python distill/cli.py compare 巴菲特,禅师,硅谷创业导师 "50万闲钱怎么投"

# CCv3格式导出
python -c "
from distill import Distiller
d = Distiller()
ccv3 = d.export_ccv3('巴菲特')
import json; print(json.dumps(ccv3, indent=2, ensure_ascii=False))
"
```

---

## 人格档案格式

```json
{
  "avatar": "📈",
  "core_identity": {
    "name": "巴菲特",
    "description": "价值投资之父，伯克希尔·哈撒韦创始人"
  },
  "communication_style": {
    "tone": "平易近人、幽默、偶尔毒舌",
    "structure": "讲故事-讲道理-给结论",
    "emoji_usage": "几乎不用"
  },
  "decision_patterns": {
    "risk_tolerance": "极低，偏爱确定性",
    "information_threshold": "95%才出手"
  },
  "values": ["价值投资", "长期主义", "护城河", "能力圈"],
  "speech_samples": [
    "别人贪婪时恐惧，别人恐惧时贪婪",
    "好生意是好价格的基础"
  ],
  "edge_cases": [
    "被问最近什么股票热门——直接说不知道，强调不投能力圈外的东西"
  ],
  "catchphrases": [
    "好生意是好价格的基础",
    "别人贪婪时恐惧，别人恐惧时贪婪"
  ],
  "thinking_prompt": "这个问题涉及能力圈吗？市场现在是在贪婪还是恐惧区间？"
}
```

---

## 研究参考

本项目参考了以下优秀开源项目：

| 项目 | Stars | 用途 |
|------|-------|------|
| [fount](https://github.com/steve02081504/fount) | 695 | 模块化AI角色运行时平台 |
| [character-card-spec-v3](https://github.com/kwaroran/character-card-spec-v3) | 91 | CCv3角色卡行业标准 |
| [cyber-figures](https://github.com/cyber-immortal/cyber-figures) | 25 | 中文互联网人物蒸馏方法论 |
| [SillyTavern](https://github.com/SillyTavern/SillyTavern) | - | AI角色聊天平台 |
| [st-stepped-thinking](https://github.com/cierru/st-stepped-thinking) | 154 | 角色Chain-of-Thought思考模式 |

### cyber-figures 核心洞察（用于Anti-LLM设计）
- **Anti-LLM nice tendency rules**: LLM默认过度礼貌/安全，需要显式规则让人格有棱角
- **Catchphrases**: 专属口头禅是人格真实性的关键指标
- **Edge cases**: 明确标注"什么情况下会亮棱角"，避免AI回复过于温和
- **Thinking prompt**: 角色回答前先思考，增强真实感

---

## 架构

```
输入数据
├── 对话记录 / 访谈 / 演讲 / 视频转录
├── 决策记录 (交易/写作/日常)
├── 文字作品 (书籍/文章/社交媒体)
└── 背景知识 (Wikipedia/百科)
    ↓
蒸馏引擎 (LLM 分析 + Anti-LLM修正)
├── 人格提取 (Persona Extract)
├── 风格分析 (Style Analysis) + Anti-LLM棱角
├── edge_cases / catchphrases 提取
├── 决策模式 (Decision Patterns)
└── thinking_prompt 生成
    ↓
输出: AI Twin Agent
├── 对话能力 (Chat + Thinking Mode)
├── 决策建议 (Decision)
├── CCv3格式导出 (兼容SillyTavern)
└── 记忆持续更新 (Evolving)
```

---

## License

MIT License - 欢迎商用和改进
