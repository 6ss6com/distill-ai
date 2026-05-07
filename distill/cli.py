"""
DistillAI 简单CLI - 多种使用方式

使用示例:
  python distill.py chat 巴菲特        # 和巴菲特聊天
  python distill.py chat 禅师 禅师问   # 问禅师一个问题
  python distill.py ask 巴菲特 "茅台还能买吗"  # 快速问答
  python distill.py scenario 投资建议  # 预设场景问答
  python distill.py debate 巴菲特 马斯克 "茅台vs特斯拉哪个更值得投资"  # 两人辩论
  python distill.py compare 孙子里斯 "要不要跳槽"  # 多人对比
  python distill.py list              # 列出所有人格
  python distill.py recommend 投资 "我有10万闲钱"  # 根据情况推荐合适人格
"""

import sys
from pathlib import Path
# Add workspace to path so minimax_client can be found
WORKSPACE = Path(r'C:\Users\Administrator\.openclaw\workspace')
sys.path.insert(0, str(WORKSPACE))
sys.path.insert(0, str(Path(__file__).parent.parent))

from distill import Distiller
from distill.presets_extended import PRESET_PERSONAS_EXTENDED

ALL_PRESETS = PRESET_PERSONAS_EXTENDED


# ============ 预设场景 ============
SCENARIOS = {
    # === 投资理财 ===
    "投资建议": "用{persona}的风格，给出投资建议。情况：{situation}",
    "选股分析": "你是{persona}，分析{stock}这只股票，给出是否值得投资的判断",
    "理财诊断": "你是{persona}，分析以下理财状况，给出优化建议：{situation}",
    "风险评估": "你是{persona}，评估以下投资风险：{situation}",

    # === 写作助手 ===
    "情书": "以{persona}的风格，写一封情书，表达{sentiment}的情感",
    "分手信": "以{persona}的风格，写一封分手信，要{tone}",
    "道歉信": "以{persona}的风格，写一封道歉信，内容：{content}",
    "演讲稿": "以{persona}的风格，写一篇{speech_type}的演讲稿，主题：{topic}",
    "朋友圈文案": "以{persona}的风格，写一条{sentiment}的朋友圈，配图是{scene}",
    "短视频脚本": "以{persona}的风格，写一个{topic}主题的短视频脚本，时长30秒",
    "小说开头": "以{persona}的风格，写一篇{genre}类型小说的开头，吸引读者",

    # === 决策顾问 ===
    "跳槽建议": "你是{persona}，分析是否应该跳槽：{situation}",
    "创业评估": "你是{persona}，评估这个创业想法的可行性：{idea}",
    "人生抉择": "你是{persona}，帮我分析这个人生选择：{choice}",
    "买房建议": "你是{persona}，给出买房建议：{situation}",

    # === 学习教育 ===
    "物理讲解": "以{persona}的风格，向小学生解释{concept}，要生动有趣",
    "历史故事": "以{persona}的风格，讲一个关于{event}的历史故事",
    "学习方法": "以{persona}的学习方法论，给出学习{subject}的建议",
    "思维训练": "以{persona}的思维方式，解决这个问题：{problem}",

    # === 心理情感 ===
    "心理咨询": "以{persona}的智慧，给我一些情感建议：{situation}",
    "职场解压": "以{persona}的风格，给职场压力建议：{situation}",
    "告别过去": "以{persona}的风格，帮助我放下{situation}",

    # === 商业经营 ===
    "营销方案": "以{persona}的思维，设计一个{s_product}的营销方案",
    "管理建议": "以{persona}的管理风格，给出团队管理建议：{situation}",
    "商业谈判": "以{persona}的谈判风格，准备一场关于{topic}的谈判",
    "品牌定位": "以{persona}的战略眼光，分析品牌定位：{brand}",

    # === 创意娱乐 ===
    "设计灵感": "以{persona}的审美，给出{design_type}的设计灵感：{brief}",
    "取名": "以{persona}的智慧，给{name_type}取一个有内涵的名字",
    "解梦": "以{persona}的风格，解这个梦的含义：{dream}",
    "算命": "以{persona}的智慧，给出命运指引：{situation}",
}


def list_personas():
    """列出所有人格"""
    personas_dir = Path(__file__).parent / "personas"
    if not personas_dir.exists():
        print("No personas found. Run distill_from_workspace() first.")
        return

    files = sorted([f.stem for f in personas_dir.glob("*.json")])

    # 按分类整理
    categories = {
        "科学家": ["爱因斯坦", "居里夫人", "特斯拉", "达芬奇"],
        "哲学家": ["苏格拉底", "尼采", "王阳明", "孔子"],
        "军事战略": ["孙子", "俾斯麦"],
        "政治领袖": ["林肯"],
        "艺术大师": ["宫崎骏", "卓别林", "莎士比亚", "金庸"],
        "商业投资": ["巴菲特"],
        "文学": ["鲁迅"],
        "侦探/虚构": ["夏洛克·福尔摩斯"],
        "原创角色": ["时间领主", "硅谷创业导师", "禅师"],
        "个人": ["金"],
    }

    print("\n" + "=" * 50)
    print("  DistillAI 可用人格 (" + str(len(files)) + "个)")
    print("=" * 50)
    for cat, names in categories.items():
        available = [n for n in names if n in files]
        if available:
            print(f"\n  【{cat}】")
            for n in available:
                print(f"    {n}")

    print("\n  【使用方式】")
    print("    python distill.py ask 巴菲特 '茅台还能买吗'")
    print("    python distill.py scenario 投资建议")
    print("    python distill.py debate 巴菲特 马斯克 '哪个更值得投资'")


def chat_persona(name: str, message: str):
    """和人格聊天"""
    d = Distiller()
    try:
        reply = d.chat(name, message)
        print(f"\n【{name}】\n{reply}")
    except FileNotFoundError:
        print(f"人格 '{name}' 不存在。请先运行: python distill.py list")


def ask_persona(name: str, question: str):
    """快速问答"""
    chat_persona(name, question)


def run_scenario(scenario_name: str, params: dict = None):
    """运行预设场景"""
    if scenario_name not in SCENARIOS:
        print(f"未知场景: {scenario_name}")
        print(f"可用场景: {list(SCENARIOS.keys())}")
        return

    d = Distiller()

    # 如果没有传参数，交互式获取
    if not params:
        print(f"\n=== 场景: {scenario_name} ===")
        # 从场景描述中提取变量
        template = SCENARIOS[scenario_name]
        vars_needed = set()
        import re
        for m in re.finditer(r'\{(\w+)\}', template):
            vars_needed.add(m.group(1))

        params = {}
        for v in vars_needed:
            if v == "persona":
                continue  # persona 单独指定
            params[v] = input(f"  {v}: ").strip()

    # 如果params里没有persona，让用户选择
    if "persona" not in params:
        print("\n选择人格 (留空推荐最合适的):")
        print("  1 巴菲特(投资)  2 禅师(智慧)  3 苏格拉底(思辨)  4 爱因斯坦(科学)")
        print("  5 孙子(战略)    6 硅谷创业导师(创业)  7 金(你自己)")
        choice = input("  选择: ").strip()
        choice_map = {
            "1": "巴菲特", "2": "禅师", "3": "苏格拉底", "4": "爱因斯坦",
            "4": "爱因斯坦", "5": "孙子", "6": "硅谷创业导师", "7": "金"
        }
        params["persona"] = choice_map.get(choice, "巴菲特")

    # 渲染模板
    template = SCENARIOS[scenario_name]
    try:
        prompt = template.format(**params)
    except KeyError as e:
        print(f"缺少参数: {e}")
        return

    print(f"\n【{params['persona']}】\n")
    reply = d.chat(params["persona"], prompt)
    print(reply)


def persona_debate(name1: str, name2: str, topic: str):
    """两人辩论"""
    d = Distiller()
    prompt = f"""你是一场辩论赛的一方。

辩题是：「{topic}」

你是「{name1}」，请从{name1}的立场出发，针对这个话题发表观点。

要求：
- 保持{name1}的说话风格和思维方式
- 提出有力的论点
- 可以反驳对方可能的观点

你的开场陈述："""

    print(f"\n=== 辩论赛 ===")
    print(f"辩题: {topic}")
    print(f"正方: {name1} | 反方: {name2}")
    print(f"\n--- 正方 {name1} 开场 ---\n")

    r1 = d.chat(name1, prompt)
    print(r1)

    counter_prompt = f"""接上辩论。

反方「{name2}」刚才说：{r1[:300]}...

现在你是「{name2}」，请从{name2}的立场反驳上述观点，并给出自己的论点。

要求：
- 保持{name2}的说话风格
- 直接针对对方的论点进行反驳
- 提出有力反例

你的反驳："""

    print(f"\n--- 反方 {name2} 反驳 ---\n")
    r2 = d.chat(name2, counter_prompt)
    print(r2)

    # 正方回应
    rebuttal = f"""继续辩论。

正方「{name1}」刚才的反驳：{r2[:300]}...

正方「{name1}」的最终回应（总结观点，回应质疑）："""
    print(f"\n--- 正方 {name1} 最终回应 ---\n")
    r3 = d.chat(name1, rebuttal)
    print(r3)


def compare_personas(names: list, question: str):
    """多人对比：同一问题，多个视角"""
    d = Distiller()
    print(f"\n=== 问题对比 ===")
    print(f"问题: {question}\n")

    results = {}
    for name in names:
        try:
            reply = d.chat(name, question)
            results[name] = reply
        except FileNotFoundError:
            results[name] = f"[人格 '{name}' 不存在]"

    for i, (name, reply) in enumerate(results.items(), 1):
        print(f"--- 【{name}】的答案 ---\n{reply}\n")
        if i < len(results):
            print("=" * 50 + "\n")


def recommend_persona(situation: str):
    """根据情况推荐最合适的人格"""
    prompt = f"""根据以下情况，推荐最合适的中国历史/现代人物或虚构角色来解决这个问题：

情况：{situation}

候选人物：
- 投资/理财问题 → 巴菲特
- 战略/竞争问题 → 孙子、俾斯麦
- 人生迷茫/情感问题 → 禅师、苏格拉底、王阳明
- 创业/商业问题 → 硅谷创业导师、巴菲特
- 科学/技术问题 → 爱因斯坦、特斯拉、达芬奇
- 文学/写作问题 → 金庸、莎士比亚
- 管理/领导问题 → 俾斯麦、孙子、曾国藩
- 学习/教育问题 → 苏格拉底（追问法）、孔子
- 艺术/创意问题 → 宫崎骏、达芬奇
- 历史/文化问题 → 金庸、鲁迅、莎士比亚

请直接给出推荐的人物名字，简要说明理由。

推荐："""

    d = Distiller()
    # 用金的人格来推荐
    reply = d.chat("金", prompt)
    print(f"\n【推荐结果】\n{reply}")


def quick_use():
    """交互式快速使用"""
    print("\n" + "=" * 50)
    print("  DistillAI 快速使用")
    print("=" * 50)
    print("  1. 和某人聊天")
    print("  2. 运行预设场景")
    print("  3. 两人辩论")
    print("  4. 多人对比")
    print("  5. 根据情况推荐人格")
    print("  0. 列出所有人格")
    print()
    choice = input("选择: ").strip()

    if choice == "1":
        name = input("人格名称: ").strip()
        q = input("问题: ").strip()
        if name and q:
            chat_persona(name, q)
        else:
            print("请输入人格名称和问题")
    elif choice == "2":
        print("\n可用场景:", ", ".join(SCENARIOS.keys()))
        s = input("场景名称: ").strip()
        if s in SCENARIOS:
            run_scenario(s)
        else:
            print("未知场景")
    elif choice == "3":
        n1 = input("正方: ").strip()
        n2 = input("反方: ").strip()
        topic = input("辩题: ").strip()
        if n1 and n2 and topic:
            persona_debate(n1, n2, topic)
    elif choice == "4":
        names = input("人格列表(逗号分隔): ").strip().split(",")
        q = input("问题: ").strip()
        if names and q:
            compare_personas([n.strip() for n in names], q)
    elif choice == "5":
        s = input("你的情况: ").strip()
        if s:
            recommend_persona(s)
    elif choice == "0":
        list_personas()
    else:
        print("无效选择")


# ============ 主入口 ============
if __name__ == "__main__":
    if len(sys.argv) == 1:
        quick_use()
        sys.exit()

    cmd = sys.argv[1].lower()

    if cmd == "list":
        list_personas()

    elif cmd == "chat":
        # python distill.py chat 巴菲特 "问题内容"
        if len(sys.argv) >= 3:
            name = sys.argv[2]
            message = sys.argv[3] if len(sys.argv) >= 4 else input("问题: ")
            chat_persona(name, message)
        else:
            print("用法: python distill.py chat <人格> <问题>")

    elif cmd == "ask":
        # python distill.py ask 巴菲特 "茅台还能买吗"
        if len(sys.argv) >= 4:
            name = sys.argv[2]
            question = sys.argv[3]
            ask_persona(name, question)
        else:
            print("用法: python distill.py ask <人格> <问题>")

    elif cmd == "scenario":
        # python distill.py scenario 投资建议 persona=巴菲特 situation=...
        scenario_name = sys.argv[2] if len(sys.argv) >= 3 else input("场景: ").strip()
        if scenario_name not in SCENARIOS:
            print("可用场景:")
            for s in SCENARIOS:
                print(f"  {s}")
            sys.exit()

        # 解析参数
        params = {}
        for arg in sys.argv[3:]:
            if "=" in arg:
                k, v = arg.split("=", 1)
                params[k.strip()] = v.strip()

        run_scenario(scenario_name, params if params else None)

    elif cmd == "debate":
        # python distill.py debate 巴菲特 马斯克 "哪个更值得投资"
        if len(sys.argv) >= 5:
            name1, name2 = sys.argv[2], sys.argv[3]
            topic = sys.argv[4]
            persona_debate(name1, name2, topic)
        else:
            print("用法: python distill.py debate <正方> <反方> <辩题>")

    elif cmd == "compare":
        # python distill.py compare 巴菲特,禅师,苏格拉底 "10万闲钱怎么投"
        if len(sys.argv) >= 3:
            names = [n.strip() for n in sys.argv[2].split(",")]
            question = sys.argv[3] if len(sys.argv) >= 4 else input("问题: ")
            compare_personas(names, question)
        else:
            print("用法: python distill.py compare <人格1,人格2,...> <问题>")

    elif cmd == "recommend":
        # python distill.py recommend "我有10万闲钱"
        situation = sys.argv[2] if len(sys.argv) >= 3 else input("你的情况: ")
        recommend_persona(situation)

    elif cmd == "help":
        print(__doc__)

    else:
        print(f"未知命令: {cmd}")
        print("用法:")
        print("  python distill.py list                        # 列出人格")
        print("  python distill.py chat <人格> <问题>         # 和人格聊天")
        print("  python distill.py ask <人格> <问题>          # 快速问答")
        print("  python distill.py scenario <场景名>           # 运行预设场景")
        print("  python distill.py debate <正方> <反方> <辩题> # 两人辩论")
        print("  python distill.py compare <人格1,2> <问题>   # 多视角对比")
        print("  python distill.py recommend <情况>           # 推荐适合的人格")
        print()
        print("场景列表:")
        for s in SCENARIOS:
            print(f"  {s}")