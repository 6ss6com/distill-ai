"""
DistillAI CLI - Bilingual Chat / 多语言人格对话系统
Supports: 中文 English 日本語

Usage:
  python distill.py ask 巴菲特 "茅台值得买吗"        # 中文
  python distill.py ask Buffett "Is Moutai worth it?"  # English
  python distill.py random "生命的意义是什么"         # 随机人格
  python distill.py distill 鲁迅 "中国现代文学家"   # 蒸馏自定义人格
  python distill.py list --lang en                  # English persona list
  python distill.py --config                        # Show config

Platform: Windows / macOS / Linux 自动适配
"""

import sys
import os
import random
import platform
from pathlib import Path

# ---- Path setup (cross-platform) ----
WORKSPACE = Path(r"C:\Users\Administrator\.openclaw\workspace")
if not WORKSPACE.exists():
    WORKSPACE = Path.home() / ".openclaw" / "workspace"
if not WORKSPACE.exists():
    WORKSPACE = Path(__file__).parent.parent

sys.path.insert(0, str(WORKSPACE))
sys.path.insert(0, str(Path(__file__).parent.parent))

from distill import Distiller

# ---- Language detection ----
def detect_lang(text: str) -> str:
    """Auto-detect language from text"""
    # Count Chinese characters
    chinese = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
    japanese = sum(1 for c in text if '\u3040' <= c <= '\u309f' or '\u30a0' <= c <= '\u30ff')
    total = len(text.strip())
    if total == 0:
        return "zh"
    if chinese / total > 0.3:
        return "zh"
    if japanese / total > 0.3:
        return "ja"
    return "en"


# ---- Bilingual strings ----
STRINGS = {
    "zh": {
        "title": "DistillAI - 人格蒸馏对话系统",
        "avail": "可用人格",
        "ask_usage": "用法: python distill.py ask <人格> <问题>",
        "chat_usage": "用法: python distill.py chat <人格>",
        "not_found": "人格 '{name}' 不存在，请先 python distill.py list",
        "蒸馏完成": "人格蒸馏完成！",
        "沟通风格": "沟通风格",
        "价值观": "价值观",
        "现在可以": "现在可以对话",
        "random_title": "随机人格",
        "selected": "随机选中了",
        "debate_title": "辩论赛",
        "pos": "正方",
        "neg": "反方",
        "topic": "辩题",
        "opening": "开场",
        "counter": "反驳",
        "final": "最终回应",
        "compare_title": "多视角对比",
        "answer_from": "的答案",
        "recommend_title": "人格推荐",
        "situation": "你的情况",
        "recommended": "推荐",
        "scenarios": "可用场景",
        "list_header": "列出所有人格",
        "config_header": "系统配置",
        "platform": "平台",
        "personas_count": "人格总数",
        "help_cmds": "可用命令",
        "unknown_cmd": "未知命令",
    },
    "en": {
        "title": "DistillAI - Persona Distillation Chat",
        "avail": "Available Personas",
        "ask_usage": "Usage: python distill.py ask <persona> <question>",
        "chat_usage": "Usage: python distill.py chat <persona>",
        "not_found": "Persona '{name}' not found. Run: python distill.py list",
        "distill_done": "Persona distilled successfully!",
        "style": "Communication Style",
        "values": "Values",
        "now_chat": "Now chat with:",
        "random_title": "Random Persona",
        "selected": "Randomly selected",
        "debate_title": "Debate",
        "pos": "Pro",
        "neg": "Con",
        "topic": "Topic",
        "opening": "Opening",
        "counter": "Rebuttal",
        "final": "Final",
        "compare_title": "Multi-Perspective",
        "answer_from": "'s Answer",
        "recommend_title": "Persona Recommender",
        "situation": "Your situation",
        "recommended": "Recommended",
        "scenarios": "Available Scenarios",
        "list_header": "List All Personas",
        "config_header": "System Config",
        "platform": "Platform",
        "personas_count": "Total Personas",
        "help_cmds": "Available Commands",
        "unknown_cmd": "Unknown command",
    }
}

def _(key: str, lang: str = "zh") -> str:
    return STRINGS.get(lang, STRINGS["zh"]).get(key, STRINGS["zh"].get(key, key))


# ---- Config ----
CONFIG_FILE = Path(__file__).parent / "config.json"

DEFAULT_CONFIG = {
    "lang": "auto",  # auto / zh / en / ja
    "default_persona": "金",
    "random_exclude": ["金"],
    "theme": "default",  # default / dark
}

def load_config() -> dict:
    if CONFIG_FILE.exists():
        try:
            import json
            return {**DEFAULT_CONFIG, **json.loads(CONFIG_FILE.read_text())}
        except:
            pass
    return DEFAULT_CONFIG.copy()

def save_config(cfg: dict):
    try:
        import json
        CONFIG_FILE.write_text(json.dumps(cfg, indent=2, ensure_ascii=False))
    except:
        pass


# ---- Personas ----
def list_personas(lang: str = "zh"):
    personas_dir = Path(__file__).parent / "personas"
    files = sorted([f.stem for f in personas_dir.glob("*.json") if f.suffix == ".json"])

    cfg = load_config()
    exclude = cfg.get("random_exclude", ["金"])

    print(f"\n{'='*55}")
    print(f"  DistillAI  {_( 'title', lang)} ({len(files)} {_( 'personas_count', lang)})")
    print(f"  Platform: {platform.system()} | Python: {platform.python_version()}")
    print(f"{'='*55}")

    categories_zh = {
        "剑士/冒险": ["苍炎剑士"],
        "法师/魔法": ["银发法师", "青云剑仙"],
        "赛博/科幻": ["幽灵黑客", "星际舰长"],
        "东方玄幻": ["九尾灵狐"],
        "治愈/日常": ["深夜食堂老板", "森林精灵", "树洞姐姐"],
        "神秘/暗黑": ["赏金死神", "命运占卜师", "沙雕网友"],
        "科学家": ["爱因斯坦", "居里夫人", "特斯拉", "达芬奇"],
        "哲学家": ["苏格拉底", "尼采", "王阳明", "孔子"],
        "军事战略": ["孙子", "俾斯麦"],
        "政治领袖": ["林肯"],
        "艺术大师": ["宫崎骏", "卓别林", "莎士比亚", "金庸"],
        "商业投资": ["巴菲特"],
        "公版角色": ["夏洛克·福尔摩斯"],
        "原创角色": ["时间领主", "硅谷创业导师", "禅师"],
        "个人蒸馏": ["金"],
    }

    categories_en = {
        "Warrior/Adventure": ["苍炎剑士"],
        "Magic/Fantasy": ["银发法师", "青云剑仙"],
        "Cyber/Sci-fi": ["幽灵黑客", "星际舰长"],
        "Eastern Fantasy": ["九尾灵狐"],
        "Healing/Daily": ["深夜食堂老板", "森林精灵", "树洞姐姐"],
        "Dark/Mysterious": ["赏金死神", "命运占卜师", "沙雕网友"],
        "Scientist": ["爱因斯坦", "居里夫人", "特斯拉", "达芬奇"],
        "Philosopher": ["苏格拉底", "尼采", "王阳明", "孔子"],
        "Military/Strategy": ["孙子", "俾斯麦"],
        "Political Leader": ["林肯"],
        "Art Master": ["宫崎骏", "卓别林", "莎士比亚", "金庸"],
        "Business/Invest": ["巴菲特"],
        "Public Domain": ["夏洛克·福尔摩斯"],
        "Original": ["时间领主", "硅谷创业导师", "禅师"],
        "Personal": ["金"],
    }

    categories = categories_en if lang == "en" else categories_zh

    for cat, names in categories.items():
        available = [n for n in names if n in files and n not in exclude]
        if available:
            print(f"\n  [{cat}]")
            for n in available:
                try:
                    from distill import Persona
                    p = Persona(n, {})
                    p = load_persona_raw(n)
                    avatar = p.get("avatar", "")
                    if avatar:
                        print(f"    {avatar} {n}")
                    else:
                        print(f"    - {n}")
                except:
                    print(f"    - {n}")

    print(f"\n{'='*55}")
    print(f"  {_( 'help_cmds', lang)}:")
    print(f"    ask <persona> <question>     - Quick Q&A")
    print(f"    chat <persona>               - Interactive chat")
    print(f"    random <question>            - Random persona answers")
    print(f"    distill <name> <desc>        - Distill custom persona")
    print(f"    debate <A> <B> <topic>      - Two-person debate")
    print(f"    compare <A,B> <question>    - Multi-perspective")
    print(f"    recommend <situation>       - Recommend a persona")
    print(f"    list --lang en              - English persona list")


def load_persona_raw(name: str) -> dict:
    path = Path(__file__).parent / "personas" / f"{name}.json"
    if not path.exists():
        return {}
    import json
    return json.loads(path.read_text(encoding="utf-8"))


def chat_persona(name: str, message: str, lang: str = "auto"):
    """Chat with a persona, auto-detecting language"""
    if lang == "auto":
        lang = detect_lang(message)

    d = Distiller()
    try:
        reply = d.chat(name, message)
        reply_lang = detect_lang(reply)

        # Show avatar if available
        try:
            p = load_persona_raw(name)
            avatar = p.get("avatar", "")
        except:
            avatar = ""

        if avatar:
            print(f"\n{avatar} 【{name}】\n{reply}")
        else:
            print(f"\n【{name}】\n{reply}")
    except FileNotFoundError:
        print(_("not_found", lang).format(name=name))


def cmd_ask(args, lang: str = "auto"):
    if lang == "auto":
        lang = detect_lang(args.question)
    chat_persona(args.persona, args.question, lang)


def cmd_random(args, lang: str = "auto"):
    if lang == "auto":
        lang = detect_lang(args.question) if args.question else "zh"

    personas_dir = Path(__file__).parent / "personas"
    cfg = load_config()
    exclude = cfg.get("random_exclude", ["金"])

    all_p = [f.stem for f in personas_dir.glob("*.json") if f.stem not in exclude]
    chosen = random.choice(all_p)

    avatar = ""
    try:
        p = load_persona_raw(chosen)
        avatar = p.get("avatar", "")
    except:
        pass

    print(f"\n  [Random] {chosen} {'-' if not avatar else avatar}\n")
    chat_persona(chosen, args.question or "随便聊聊", lang)


def cmd_distill(args, lang: str = "auto"):
    if lang == "auto":
        lang = "zh"

    name = args.name.strip()
    desc = args.description.strip() if args.description else ""

    print(f"\n  Distilling custom persona: {name}...")
    if desc:
        print(f"  Description: {desc[:50]}...")

    d = Distiller()
    try:
        persona = d.distill_from_files(name, [], desc)
        avatar = getattr(persona, 'avatar', '') or ""
        print(f"\n  [{avatar} {name}] Distilled successfully!")
        print(f"  Style: {persona.communication_style.get('tone', 'N/A')}")
        print(f"  Values: {', '.join(persona.values[:3])}")
        print(f"\n  Now chat: python distill.py chat {name}")
    except Exception as e:
        print(f"  Distillation failed: {e}")


def cmd_debate(args, lang: str = "auto"):
    if lang == "auto":
        lang = detect_lang(args.topic)

    d = Distiller()
    n1, n2, topic = args.pos, args.neg, args.topic

    print(f"\n{'='*55}")
    print(f"  Debate: {args.topic}")
    print(f"  {n1}(+) vs {n2}(-)")
    print(f"{'='*55}\n")

    # Get avatar
    p1 = load_persona_raw(n1)
    p2 = load_persona_raw(n2)
    a1 = p1.get("avatar", "")
    a2 = p2.get("avatar", "")

    r1 = d.chat(n1, f"你是{n1}，请对「{topic}」发表正方开场陈述。保持{n1}的说话风格。")
    print(f"--- {a1} {n1} 开场陈述 ---\n{r1}\n")

    r2 = d.chat(n2, f"你是{n2}，正方{n1}说：{r1[:200]}...\n请作为反方反驳，然后给出你的论点。")
    print(f"--- {a2} {n2} 反驳+论点 ---\n{r2}\n")

    r3 = d.chat(n1, f"继续辩论。反方{n2}说：{r2[:200]}...\n正方{n1}最终回应。")
    print(f"--- {a1} {n1} 最终回应 ---\n{r3}\n")


def cmd_compare(args, lang: str = "auto"):
    if lang == "auto":
        lang = detect_lang(args.question)

    names = [n.strip() for n in args.personas.split(",")]
    q = args.question

    print(f"\n{'='*55}")
    print(f"  Question: {q}")
    print(f"{'='*55}\n")

    d = Distiller()
    for name in names:
        avatar = ""
        try:
            p = load_persona_raw(name)
            avatar = p.get("avatar", "")
        except:
            pass
        try:
            reply = d.chat(name, q)
            print(f"--- {avatar} {name} ---\n{reply}\n")
        except FileNotFoundError:
            print(f"[{name}] not found\n")


def cmd_recommend(args, lang: str = "auto"):
    if lang == "auto":
        lang = detect_lang(args.situation)

    print(f"\n  Analyzing: {args.situation[:50]}...\n")

    prompt = f"""根据用户情况，推荐最合适的DistillAI人格。

情况：{args.situation}

候选（选1-2个最合适的）：
- 投资理财 → 巴菲特
- 战略竞争 → 孙子、俾斯麦
- 人生迷茫/情感 → 禅师、苏格拉底、王阳明
- 创业商业 → 硅谷创业导师、巴菲特
- 科学问题 → 爱因斯坦、特斯拉、达芬奇
- 文学写作 → 金庸、莎士比亚
- 管理领导 → 俾斯麦、孙子
- 学习教育 → 苏格拉底、孔子
- 游戏动漫风格 → 苍炎剑士、银发法师、幽灵黑客、九尾灵狐
- 治愈日常 → 深夜食堂老板、森林精灵、树洞姐姐
- 神秘暗黑 → 赏金死神、命运占卜师

请直接给出推荐的人格名称和推荐理由（1-3句话）。

推荐："""

    d = Distiller()
    reply = d.chat("金", prompt)
    print(f"  {reply}")


# ---- CLI Entry ----
import argparse

def main():
    parser = argparse.ArgumentParser(
        description="DistillAI - Bilingual Persona Chat CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  中文: python distill.py ask 巴菲特 "茅台还能买吗"
  英文: python distill.py ask Buffett "Is Moutai worth it?"
  随机: python distill.py random "生命的意义是什么"
  辩论: python distill.py debate 巴菲特 禅师 "要不要辞职创业"
  对比: python distill.py compare 巴菲特,禅师,硅谷创业导师 "10万闲钱怎么投"
  推荐: python distill.py recommend "我最近很迷茫，不知道该怎么做"
  自定义: python distill.py distill 我的导师 "一个严厉但关心学生的人"
  列表: python distill.py list --lang en
        """
    )
    parser.add_argument("--lang", "-l", default="auto",
                       help="Language: auto, zh, en (default: auto)")

    sub = parser.add_subparsers(dest="cmd")

    # ask
    p = sub.add_parser("ask", help="Quick Q&A with a persona")
    p.add_argument("persona", help="Persona name")
    p.add_argument("question", help="Question", nargs="?")

    # chat
    p = sub.add_parser("chat", help="Interactive chat with persona")
    p.add_argument("persona", help="Persona name")

    # random
    p = sub.add_parser("random", help="Random persona answers")
    p.add_argument("question", help="Question", nargs="?")

    # distill
    p = sub.add_parser("distill", help="Distill custom persona")
    p.add_argument("name", help="Persona name")
    p.add_argument("description", help="Persona description", nargs="?")

    # debate
    p = sub.add_parser("debate", help="Two-person debate")
    p.add_argument("pos", help="Pro persona")
    p.add_argument("neg", help="Con persona")
    p.add_argument("topic", help="Debate topic", nargs="?", default="这个问题")

    # compare
    p = sub.add_parser("compare", help="Multi-perspective comparison")
    p.add_argument("personas", help="Comma-separated persona names")
    p.add_argument("question", help="Question", nargs="?")

    # recommend
    p = sub.add_parser("recommend", help="Recommend best persona")
    p.add_argument("situation", help="User situation", nargs="?")

    # list
    p = sub.add_parser("list", help="List all personas")

    # config
    p = sub.add_parser("config", help="Show/set config")
    p.add_argument("--set", nargs="?", help="Set config value, e.g. --set lang=en")

    args = parser.parse_args()

    lang = args.lang if args.lang != "auto" else "auto"

    if args.cmd is None:
        parser.print_help()
        return

    if args.cmd == "list":
        list_personas(lang)
    elif args.cmd == "ask":
        if not args.question:
            args.question = input("Question: ").strip()
        cmd_ask(args, lang)
    elif args.cmd == "chat":
        print(f"\n[Interactive chat with {args.persona}, type 'exit' to quit]\n")
        while True:
            q = input(f"{args.persona}> ").strip()
            if q.lower() in ("exit", "quit", "q"):
                break
            if not q:
                continue
            chat_persona(args.persona, q, lang)
    elif args.cmd == "random":
        cmd_random(args, lang)
    elif args.cmd == "distill":
        cmd_distill(args, lang)
    elif args.cmd == "debate":
        cmd_debate(args, lang)
    elif args.cmd == "compare":
        cmd_compare(args, lang)
    elif args.cmd == "recommend":
        if not args.situation:
            args.situation = input("Situation: ").strip()
        cmd_recommend(args, lang)
    elif args.cmd == "config":
        cfg = load_config()
        if args.set:
            k, v = args.set.split("=", 1)
            cfg[k.strip()] = v.strip()
            save_config(cfg)
            print(f"Set {k}={v}")
        else:
            print("\n[DistillAI Config]")
            for k, v in cfg.items():
                print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
