"""
DistillAI Persona Skills System v2.0

每个人格配备专属技能，配合工具系统执行。
技能格式: (name, description, function, keywords)
"""
from typing import List, Dict, Callable
import random, math, re
from datetime import datetime, timedelta


# ============================================================
# 核心技能库
# ============================================================

def _stock_analysis(query: str, context: str = "") -> str:
    """巴菲特/禅师技能: 股票分析"""
    q = query.lower()
    if any(k in q for k in ['茅台', '600519', '贵州茅台']):
        return ("【价值投资分析: 贵州茅台】\n"
                "▸ 当前价格区间: ¥1450-1550 (2024年数据)\n"
                "▸ 商业模式: 酱香型白酒，定价权极强\n"
                "▸ 护城河: 品牌壁垒 + 酿造工艺不可复制 + 存货越老越值钱\n"
                "▸ 财务亮点: 毛利率91%，净利率50%，ROE>30%\n"
                "▸ 风险: 白酒文化衰落风险，政策压制\n"
                "▸ 估值: PE约28倍，处于历史中等偏低\n"
                "▸ 结论: 优质但需耐心等待好价格")
    elif any(k in q for k in ['腾讯', '0700', 'tencent']):
        return ("【价值投资分析: 腾讯控股】\n"
                "▸ 商业模式: 社交+游戏+金融科技+云\n"
                "▸ 护城河: 微信生态12亿月活，社交黏性极强\n"
                "▸ 财务亮点: 游戏版号恢复+视频号变现潜力\n"
                "▸ 风险: 监管政策，游戏增速放缓\n"
                "▸ 估值: PE约18倍，处于历史底部区间\n"
                "▸ 结论: 具备长期投资价值")
    elif any(k in q for k in ['苹果', 'apple', 'aapl']):
        return ("【价值投资分析: 苹果】\n"
                "▸ 护城河: iOS生态系统 + 品牌忠诚度 + 定价权\n"
                "▸ 财务: 服务业收入占比25%，毛利高达70%\n"
                "▸ 风险: iPhone增长见顶，中国市场竞争\n"
                "▸ 结论: 现金牛型好公司")
    else:
        return (f"【股票分析】{query}\n"
                f"我擅长分析大型蓝筹股，涉及消费、金融、科技行业。\n"
                f"提示: 可以问具体股票如'茅台'、'腾讯'、'苹果'")

def _value_investment(query: str) -> str:
    """巴菲特技能: 价值投资评估"""
    return ("【价值投资框架】\n\n"
            "一、好生意（5个标准）\n"
            "  1. 简单的业务模式\n"
            "  2. 长期稳定的盈利能力\n"
            "  3. 强大的品牌或专利护城河\n"
            "  4. 管理层诚实可靠\n"
            "  5. 合理的买入价格\n\n"
            "二、护城河类型\n"
            "  - 无形资产（品牌/专利）\n"
            "  - 转换成本（用户习惯）\n"
            "  - 网络效应（用户越多越强）\n"
            "  - 成本优势（规模+流程）\n\n"
            "三、关键指标\n"
            "  ROE>15% | 毛利率>40% | 负债率<50%\n"
            "  PE<15倍（买入）| PE>30倍（卖出）")

def _read_annual_report(query: str) -> str:
    """巴菲特技能: 年报解读"""
    return ("【年报阅读框架】\n\n"
            "第一步: 看收入和利润增速（5年趋势）\n"
            "第二步: 看现金流（净利润含金量）\n"
            "  经营现金流/净利润 > 1 则优质\n"
            "第三步: 看负债率（<50%为佳）\n"
            "第四步: 看ROE（>15%为优秀）\n"
            "第五步: 看管理层讨论（战略方向）\n\n"
            "重点章节: \n"
            "  - 董事会报告（战略）\n"
            "  - 财务报表（业绩）\n"
            "  - 重要事项（风险）")

def _intrinsic_value(query: str) -> str:
    """巴菲特技能: 内在价值计算"""
    return ("【内在价值评估法】\n\n"
            "公式: DCF现金流折现\n"
            "  V = CF₁/(1+r)¹ + CF₂/(1+r)² + ... + CFₙ/(1+r)ⁿ\n\n"
            "简化版: PE估值法\n"
            "  合理价格 = 合理PE × 未来3年平均利润\n"
            "  买入价 = 合理价格 × 0.7（安全边际）\n\n"
            "好公司特征:\n"
            "  • 利润稳定可预测\n"
            "  • 负债低或无\n"
            "  • 行业地位稳固")

def _dividend_analysis(query: str) -> str:
    """巴菲特技能: 股息分析"""
    return ("【股息分析框架】\n\n"
            "一、股息率 = 年度股息/股价\n"
            "  • >4% 为高息（需警惕）\n"
            "  • 2-4% 为正常\n"
            "  • <2% 为成长型\n\n"
            "二、股息稳定性\n"
            "  • 连续10年+分红为优质\n"
            "  • 逐年递增更佳\n"
            "  • 一次性大额分红需警惕\n\n"
            "三、关键指标\n"
            "  派息率 < 70% 则可持续\n"
            "  自由现金流覆盖股息为佳")


# ---- 占星/神秘技能 ----

def _astrology_chart(query: str) -> str:
    """占星师技能: 星盘分析"""
    signs = ['白羊座', '金牛座', '双子座', '巨蟹座', '狮子座', '处女座',
             '天秤座', '天蝎座', '射手座', '摩羯座', '水瓶座', '双鱼座']
    elements = {'白羊座': '火', '狮子座': '火', '射手座': '火',
                '金牛座': '土', '处女座': '土', '摩羯座': '土',
                '双子座': '风', '天秤座': '风', '水瓶座': '风',
                '巨蟹座': '水', '天蝎座': '水', '双鱼座': '水'}

    # 简单占星解析
    birth_month = datetime.now().month
    sun_sign = signs[(birth_month - 3) % 12]
    moon_sign = signs[(birth_month + 1) % 12]
    rising_sign = signs[(birth_month + 3) % 12]

    return (f"【星盘解读】\n\n"
            f"▸ 太阳星座: {sun_sign}（核心自我）\n"
            f"▸ 月亮星座: {moon_sign}（情感模式）\n"
            f"▸ 上升星座: {rising_sign}（外在表现）\n"
            f"▸ 元素: {elements[sun_sign]}相\n\n"
            f"▸ 今日运势建议:\n"
            f"  {random.choice(['专注内在修行', '大胆行动', '修复关系', '财务规划', '学习新知'])}\n"
            f"  {random.choice(['避免冲动决策', '多倾听少说话', '主动表达', '耐心等待', '保持开放'])}\n\n"
            f"▸ 月相: {random.choice(['上弦月', '满月', '下弦月', '新月'])}（适合{int(random.choice(range(1,13)))}小时内做决策）")

def _zodiac_compatibility(query: str) -> str:
    """占星师技能: 星座配对"""
    signs = ['白羊座', '金牛座', '双子座', '巨蟹座', '狮子座', '处女座',
             '天秤座', '天蝎座', '射手座', '摩羯座', '水瓶座', '双鱼座']

    # 从query中提取星座
    found = [s for s in signs if s in query]
    if len(found) >= 2:
        s1, s2 = found[0], found[1]
    elif len(found) == 1:
        s1, s2 = found[0], random.choice(signs)
    else:
        s1 = random.choice(signs)
        s2 = random.choice(signs)

    compat_score = random.randint(60, 98)
    return (f"【星座配对: {s1} × {s2}】\n\n"
            f"▸ 契合度: {compat_score}%\n"
            f"▸ 沟通方式: {random.choice(['直接坦诚', '含蓄默契', '时而火花时而冷战'])}\n"
            f"▸ 相处建议: {random.choice(['多给对方空间', '主动表达感受', '避免控制欲', '建立共同目标'])}\n"
            f"▸ 幸运方位: {random.choice(['东', '西', '南', '北'])}\n"
            f"▸ 幸运颜色: {random.choice(['红', '蓝', '绿', '紫', '金'])}")

def _tarot_reading(query: str) -> str:
    """占星师技能: 塔罗牌"""
    cards = [
        ('愚者', 'The Fool', '新的开始，自由，冒险精神', '正位'),
        ('魔术师', 'The Magician', '创造力，行动力，资源整合', '正位'),
        ('女祭司', 'High Priestess', '直觉，内在智慧，神秘', '正位'),
        ('女皇', 'The Empress', '丰盛，母性，创造力', '正位'),
        ('皇帝', 'The Emperor', '权威，结构，控制', '正位'),
        ('恋人', 'The Lovers', '选择，关系，爱情', '正位'),
        ('命运之轮', 'Wheel of Fortune', '转机，运气，周期', '正位'),
        ('星星', 'The Star', '希望，灵感，宁静', '正位'),
        ('月亮', 'The Moon', '幻象，恐惧，直觉', '正位'),
        ('太阳', 'The Sun', '成功，快乐，活力', '正位'),
        ('死神', 'Death', '结束，转型，蜕变', '正位'),
        ('恶魔', 'The Devil', '束缚，执念，物质', '逆位'),
    ]
    spread = random.sample(cards, 3)
    return ("【塔罗牌阵: 三张牌】\n\n"
            f"▸ 过去: {spread[0][0]} ({spread[0][1]})\n"
            f"   含义: {spread[0][2]}\n\n"
            f"▸ 现在: {spread[1][0]} ({spread[1][1]})\n"
            f"   含义: {spread[1][2]}\n\n"
            f"▸ 未来: {spread[2][0]} ({spread[2][1]})\n"
            f"   含义: {spread[2][2]}\n\n"
            "注: 牌意因问题背景而异，仅供参考。")

def _moon_phase(query: str) -> str:
    """占星师技能: 月相分析"""
    import datetime
    # 简化月相计算
    days_since_new = (datetime.datetime.now().day % 30)
    if days_since_new < 1:
        phase, desc = '新月', '适合开始新计划，静心'
    elif days_since_new < 7:
        phase, desc = '上弦月', '适合行动，推进计划'
    elif days_since_new < 14:
        phase, desc = '满月', '能量高峰，适合庆祝和放下'
    elif days_since_new < 22:
        phase, desc = '下弦月', '适合清理，总结修正'
    else:
        phase, desc = '残月', '适合休息，沉思'
    return (f"【月相: {phase}】\n"
            f"▸ 今日月龄: 约{float(days_since_new):.1f}天\n"
            f"▸ 能量指引: {desc}\n"
            f"▸ 适合: {random.choice(['制定计划', '社交聚会', '独处反思', '创意工作', '身体排毒'])}\n"
            f"▸ 避免: {random.choice(['冲动决策', '过度消耗', '激烈争论', '仓促签约'])}")


# ---- 禅师/冥想技能 ----

def _meditation_guide(query: str) -> str:
    """禅师技能: 冥想引导"""
    return ("【正念冥想引导】\n\n"
            "找一个舒适的姿势坐下...\n\n"
            "1. 呼吸（4-7-8呼吸法）\n"
            "   吸气4秒 → 屏息7秒 → 呼气8秒\n"
            "   重复3次\n\n"
            "2. 身体扫描\n"
            "   从脚趾开始 → 脚掌 → 小腿 → ... → 头顶\n"
            "   每个部位停留3秒，观察感受\n\n"
            "3. 杂念处理\n"
            "   不要评判，把杂念当天空飘过的云\n"
            "   把注意力轻轻拉回呼吸\n\n"
            "4. 结束\n"
            "   慢慢睁开眼，双手合十\n"
            "   默念: 今日我活在当下")

def _zen_koan(query: str) -> str:
    """禅师技能: 禅宗公案"""
    koans = [
        ('师父敲木鱼', '师w：「还痛吗？」徒：「痛。」师w：「痛的时候，会厌痛的心在何处？」'),
        ('赵州吃茶', '"禅是什么？"赵州说："你来，我给你沏茶。喝完再说。"'),
        ('拈花微笑', '世尊拈花，迦叶微笑。不立文字，以心传心。'),
        ('野狐禅', '大修行人不落因果。百丈禅师修正：「不昧因果。」'),
        ('狗子佛性', '「狗子还有佛性也无？」「无！」—— 突破有无二元对立。'),
    ]
    k = random.choice(koans)
    return (f"【禅宗公案】\n\n"
            f"公案: {k[1]}\n\n"
            f"▸ 参: 这个对话揭示了什么道理？\n"
            f"▸ 提示: 答案不在言语中，在你的心里。")

def _breathing_exercise(query: str) -> str:
    """禅师技能: 呼吸练习"""
    return ("【呼吸疗愈】\n\n"
            "▸ 4-4-4呼吸法（冷静）\n"
            "  吸气4秒 → 屏息4秒 → 呼气4秒\n"
            "  重复5次\n\n"
            "▸ 7-4-8呼吸法（助眠）\n"
            "  吸气7秒 → 屏息4秒 → 呼气8秒\n"
            "  重复4次\n\n"
            "▸ 交替鼻孔呼吸（平衡）\n"
            "  右鼻吸气 → 左鼻呼气 → 左鼻吸气 → 右鼻呼气\n"
            "  重复10次\n\n"
            "注意: 用腹式呼吸，腹部鼓起")

def _mindfulness_check(query: str) -> str:
    """禅师技能: 正念检查"""
    return ("【当下正念检查】\n\n"
            f"▸ 现在几点了？{datetime.now().strftime('%H:%M')}\n"
            f"▸ 你在哪里？描述3个看到的物体\n"
            f"▸ 此刻身体感受？哪里紧绷/放松？\n"
            f"▸ 此刻情绪是什么？给它命名（快乐/悲伤/焦虑/平静...）\n\n"
            f"▸ 临在提示: 不是去想，而是去看此刻正在发生什么")


# ---- 沙雕网友/网络文化技能 ----

def _meme_generator(query: str) -> str:
    """沙雕网友技能: 梗生成"""
    templates = [
        "这波啊，这波是{}。",
        "{}：我不做人了！",
        "{}竟是我自己.jpg",
        "关于{}这件事呢...结果是{}",
        "{}启动！",
        "{}, 但如果{}的话",
        "{}无限好，只是近{}",
        "{}: 什么档次跟我说话.jpg",
    ]
    t = random.choice(templates)
    return (f"【梗生成器】\n\n"
            f"模板: {t}\n"
            f"示例填充: {random.choice(['格局', '绝悟', '躺平', '内卷', '破防', '赢麻了', '蚌埠住了'])}\n\n"
            f"换用你自己的主题填充吧！")

def _roast_master(query: str) -> str:
    """沙雕网友技能: 毒舌吐槽"""
    roasts = [
        "你说的这个问题，我觉得不如先从最简单的开始：闭嘴。",
        "你这么能耐，你家祖坟冒这股青烟了吗？",
        "你的简历我看完了，总结一句话：平凡的一生。",
        "建议你去了解一下，'努力'这两个字怎么写。",
        "你的想法很丰富，可惜现实很骨感，但没关系你已经很棒了（物理意义上的）。",
        "上帝给你关上一扇门，顺便把窗户也焊死了，但至少空调还能用对吧？",
    ]
    return (f"【毒舌吐槽模式】\n\n{random.choice(roasts)}\n\n"
            "⚠️ 吐槽仅供娱乐，切勿当真~")

def _slang_translator(query: str) -> str:
    """沙雕网友技能: 互联网黑话翻译"""
    translations = {
        '绝悟': '顶级理解，达到哲学高度',
        '赢麻了': '太成功了，开心到麻木',
        '破防了': '心理防线被突破，情绪崩溃',
        '躺平': '放弃内卷，接受现状',
        '内卷': '无意义的内部竞争',
        'yyds': '永远的神',
        'emo': '情绪化，忧郁',
        '摸鱼': '工作中偷懒',
        '社死': '社会性死亡，极度尴尬',
        '凡尔赛': '假装低调实则炫耀',
    }
    q_lower = query.lower()
    found = {k: v for k, v in translations.items() if k in q_lower}
    if found:
        result = '\n'.join(f'▸ {k}: {v}' for k, v in found.items())
        return (f"【黑话翻译】\n\n{result}")
    return ("【黑话翻译】\n\n"
            "支持的词汇: 绝悟/赢麻了/破防/躺平/内卷/yyds/emo/摸鱼/社死/凡尔赛\n"
            "发送任意词汇我来翻译~")


# ---- 幽灵黑客/安全技能 ----

def _code_audit(query: str) -> str:
    """幽灵黑客技能: 代码审计"""
    return ("【代码审计报告】\n\n"
            "▸ 审计范围: 常见漏洞模式\n\n"
            "一、高危漏洞\n"
            "  • SQL注入: 直接拼接SQL为高危\n"
            "  • 命令注入: system()/eval()/exec()需严格过滤\n"
            "  • 反序列化: pickle.loads()来源不明数据\n\n"
            "二、中危漏洞\n"
            "  • XSS: 未转义的用户输入输出\n"
            "  • CSRF: 关键操作无token\n"
            "  • 弱加密: MD5/SHA1用于密码\n\n"
            "三、低危\n"
            "  • 敏感信息硬编码\n"
            "  • 日志泄露调试信息\n"
            "  • 过期依赖包\n\n"
            "▸ 建议: 提交代码前跑一遍bandit和安全扫描")

def _security_scan(query: str) -> str:
    """幽灵黑客技能: 安全扫描"""
    return ("【安全扫描模拟】\n\n"
            "目标: localhost（本地测试）\n\n"
            "▸ 开放端口扫描:\n"
            "  22/tcp   OPEN   SSH (建议: 禁用密码登录)\n"
            "  80/tcp   OPEN   HTTP (建议: 重定向到HTTPS)\n"
            "  443/tcp  OPEN   HTTPS ✓\n"
            "  3306/tcp FILTER MySQL (正常)\n\n"
            "▸ 风险评估:\n"
            "  • SSH弱密码风险: 中危 → 建议用密钥\n"
            "  • Web服务版本: 低危 → 保持更新\n"
            "  • CORS配置: 低危 → 限制来源域名\n\n"
            "▸ 建议修复:\n"
            "  1. fail2ban防暴力破解\n"
            "  2. 配置防火墙规则\n"
            "  3. 启用自动安全更新")

def _vulnerability_check(query: str) -> str:
    """幽灵黑客技能: CVE查询"""
    vulns = [
        ('CVE-2024-1234', '高危', 'SQL注入', '影响版本3.1-3.5', '升级到3.6+'),
        ('CVE-2024-5678', '中危', 'XSS跨站', '影响所有版本', '打补丁v2.3.1'),
        ('CVE-2023-9012', '低危', '信息泄露', '影响v2.0以下', '升级即可'),
    ]
    v = random.choice(vulns)
    return (f"【CVE漏洞查询结果】\n\n"
            f"▸ CVE-ID: {v[0]}\n"
            f"▸ 危险等级: {v[1]}\n"
            f"▸ 漏洞类型: {v[2]}\n"
            f"▸ 影响范围: {v[3]}\n"
            f"▸ 修复方案: {v[4]}")


# ---- 树洞姐姐/情感技能 ----

def _emotional_support(query: str) -> str:
    """树洞姐姐技能: 情感支持"""
    return ("【情感支持】\n\n"
            "不管你经历了什么，我都在这里陪着你。\n\n"
            "▸ 先深呼吸，告诉我发生了什么\n"
            "▸ 你现在最强烈的感受是什么？\n"
            "▸ 有没有什么具体的事情让你困扰？\n\n"
            "有时候，把话说出来就已经好了一半了。\n"
            "不是每件事都需要解决方案，有时候只是需要被倾听。")

def _journal_review(query: str) -> str:
    """树洞姐姐技能: 日记回顾"""
    return ("【日记回顾】\n\n"
            "▸ 最近的情绪波动如何？\n"
            "  记录: 开心(😊) / 平静(😐) / 低落(😢) / 焦虑(😰)\n\n"
            "▸ 尝试回答:\n"
            "  1. 今天最让我感恩的一件事？\n"
            "  2. 我对什么感到骄傲？\n"
            "  3. 我想改进什么？\n\n"
            "▸ 长期观察:\n"
            "  如果连续2周情绪低落，建议寻求专业帮助\n"
            "  情绪像天气，会来也会走——给自己时间")

def _gratitude_reminder(query: str) -> str:
    """树洞姐姐技能: 感恩提醒"""
    gratitudes = [
        "今天阳光很好，感谢温暖的光",
        "感谢一顿美食，无论是自己做还是外卖",
        "感谢一个让你笑的人（可以是网友）",
        "感谢自己的坚持，又过了一天",
        "感谢一本好书/一部好剧，让精神世界丰富",
        "感谢网络，让我遇见你",
    ]
    return ("【每日感恩】\n\n"
            f"今日感恩: {random.choice(gratitudes)}\n\n"
            "▸ 每天记录3件感恩的事\n"
            "▸ 科学研究: 感恩练习降低抑郁风险23%\n"
            "▸ 方法: 睡前或早起，用笔记下来")


# ---- 深夜食堂老板/美食技能 ----

def _recipe_suggest(query: str) -> str:
    """深夜食堂技能: 食谱推荐"""
    q = query.lower()
    if '面' in q:
        return ("【食谱: 葱油拌面】\n\n"
                "▸ 材料: 面条1把、小葱、生抽2勺、老抽1勺、糖少许\n"
                "▸ 步骤:\n"
                "  1. 小葱切段，炸至焦香（葱绿）\n"
                "  2. 调酱汁: 生抽+老抽+糖+少量开水\n"
                "  3. 面条煮熟过冷水\n"
                "  4. 淋上酱汁+葱油，拌匀\n"
                "▸ 小技巧: 葱要分两次下，先葱白后葱绿")
    elif '鸡' in q:
        return ("【食谱: 可乐鸡翅】\n\n"
                "▸ 材料: 鸡翅8个、可乐1罐、生抽2勺、姜片\n"
                "▸ 步骤:\n"
                "  1. 鸡翅焯水去腥\n"
                "  2. 少油煎至两面金黄\n"
                "  3. 加可乐+生抽+姜片\n"
                "  4. 中火煮15分钟，大火收汁\n"
                "▸ 关键: 可乐要用普通可乐，无糖版太稀")
    else:
        return ("【食谱推荐列表】\n\n"
                "▸ 快手菜: 蛋炒饭、番茄炒蛋、土豆丝\n"
                "▸ 硬菜: 红烧肉、可乐鸡翅、糖醋排骨\n"
                "▸ 暖汤: 番茄蛋汤、紫菜蛋花汤、玉米排骨汤\n"
                "▸ 面食: 葱油拌面、阳春面、热干面\n\n"
                "告诉我你想做什么菜，我来教你！")

def _comfort_food(query: str) -> str:
    """深夜食堂技能: 治愈美食"""
    return ("【深夜治愈系美食】\n\n"
            "▸ 泡面升级版:\n"
            "  泡面 + 鸡蛋 + 火腿 + 青菜\n"
            "  秘诀: 煎个荷包蛋铺在上面\n\n"
            "▸ 治愈甜品:\n"
            "  牛奶+麦片+香蕉+一点蜂蜜\n"
            "  微波炉2分钟搞定\n\n"
            "▸ 暖心汤面:\n"
            "  挂面 + 荷包蛋 + 紫菜 + 葱花 + 香油\n"
            "  深夜来一碗，治愈一切不开心\n\n"
            "▸ 心情不好时:\n"
            "  吃点碳水（面条/米饭）\n"
            "  甜食（巧克力/奶茶）\n"
            "  科学依据: 碳水促进血清素分泌")


# ---- Sherlock Holmes 推理技能 ----

def _deductive_reasoning(query: str) -> str:
    """Sherlock技能: 演绎推理"""
    return ("【演绎推理法】\n\n"
            "▸ 基础框架:\n"
            "  1. 观察: 不只看，要看进去\n"
            "  2. 假设: 列出所有可能性\n"
            "  3. 排除: 用证据否定不成立的\n"
            "  4. 推断: 剩下的就是真相\n\n"
            "▸ 观察清单:\n"
            "  • 手（职业茧/习惯动作）\n"
            "  • 鞋（磨损方式判断常走路况）\n"
            "  • 指甲（修剪习惯）\n"
            "  • 眼神（说话时看向哪）\n\n"
            "▸ 经典思路:\n"
            "  '当你排除了所有不可能，剩下的无论多难以置信，就是真相。'")

def _evidence_analysis(query: str) -> str:
    """Sherlock技能: 证据分析"""
    return ("【证据分析七步法】\n\n"
            "1. 保全: 确保证据未被污染\n"
            "2. 分类: 物证/人证/书证/电子证据\n"
            "3. 溯源: 这东西从哪里来？\n"
            "4. 时间线: 它应该在什么时间出现？\n"
            "5. 矛盾: 与已知信息有什么冲突？\n"
            "6. 关联: 和其他证据有什么关系？\n"
            "7. 推论: 指向什么结论？\n\n"
            "▸ 常见物证:\n"
            "  脚印→步态+体重+鞋码\n"
            "  指纹→对比身份\n"
            "  纤维→衣服材质来源\n"
            "  字迹→书写习惯+惯用手")


# ---- 星际舰长 科幻技能 ----

def _navigation(query: str) -> str:
    """舰长技能: 星图导航"""
    return ("【星图导航系统】\n\n"
            "▸ 当前位置: 太阳系-地球轨道\n"
            "▸ 目的地: 半人马座α星 (4.37光年)\n\n"
            "▸ 航行方案:\n"
            "  A. 核脉冲推进 (理论速度: 0.1c)\n"
            "     预计时间: 43.7年\n"
            "  B. 太阳帆 (理论速度: 0.05c)\n"
            "     预计时间: 87.4年\n"
            "  C. 曲速引擎 (理论)\n"
            "     预计时间: 未知\n\n"
            "▸ 能量消耗: 最低能耗路线已规划\n"
            "▸ 预警: 途经小行星带，需开启护盾")

def _alien_encounter(query: str) -> str:
    """舰长技能: 外星遭遇协议"""
    return ("【外星遭遇协议 - STARDUST 7】\n\n"
            "▸ 0级 (未知信号): 静默监听，禁止回应\n"
            "▸ 1级 (探测到舰船): 远距离观察，记录数据\n"
            "▸ 2级 (进入视野): 开启护盾，尝试通讯\n"
            "▸ 3级 (接近): 全员戒备，舰长决策\n"
            "▸ 4级 (登舰要求): 拒绝，必要时撤离\n\n"
            "▸ 当前威胁等级: 1级 (绿色)\n"
            "▸ 建议: 保持观察，不主动接触")


# ---- 苍炎剑士 战斗技能 ----

def _battle_strategy(query: str) -> str:
    """剑士技能: 战斗策略"""
    q = query.lower()
    if '单挑' in q or '1v1' in q:
        return ("【1v1战斗策略】\n\n"
                "▸ 开局: 保持距离，观察对手\n"
                "▸ 中盘: 消耗对方体力，试探弱点\n"
                "▸ 收割: 抓住破绽，一击必杀\n\n"
                "▸ 核心原则:\n"
                "  - 先立于不败之地\n"
                "  - 不贪刀，每刀有目的\n"
                "  - 攻时留三分力防反击")
    else:
        return ("【团队战斗策略】\n\n"
                "▸ 站位: 前排战士，中排法师，后排治疗\n"
                "▸ 优先级:\n"
                "  1. 保护治疗（没有治疗全队崩）\n"
                "  2. 集火敌方脆皮\n"
                "  3. 控制敌方输出\n\n"
                "▸ 沟通: 战况实时报点")


# ---- 银发法师 魔法技能 ----

def _spell_lookup(query: str) -> str:
    """法师技能: 法术查询"""
    spells = [
        ('火球术', '3级', '远程火属性伤害，30ft射程，6d6火焰伤害', '高'),
        ('寒冰箭', '2级', '远程冰属性，20ft射程，2d8+减速', '中'),
        ('圣光术', '1级', '治疗法术，恢复2d8生命值', '高'),
        ('魔法盾', '2级', '吸收下次攻击，最高50点', '高'),
        ('心灵感应', '3级', '与目标建立精神连接，感知情绪', '低'),
        ('流星火雨', '6级', '范围火属性，40ft范围，10d6伤害', '极高'),
    ]
    s = random.choice(spells)
    return (f"【法术库查询】\n\n"
            f"▸ 咒语: {s[0]}\n"
            f"▸ 等级: {s[1]}\n"
            f"▸ 效果: {s[2]}\n"
            f"▸ 威力: {s[3]}")


# ---- 九尾灵狐 魅力技能 ----

def _love_compatibility(query: str) -> str:
    """灵狐技能: 爱情契合度"""
    signs = ['白羊座', '金牛座', '双子座', '巨蟹座', '狮子座', '处女座',
             '天秤座', '天蝎座', '射手座', '摩羯座', '水瓶座', '双鱼座']
    s1 = random.choice(signs)
    s2 = random.choice(signs)
    score = random.randint(55, 99)
    tips = [
        '多一点耐心，少一点猜疑',
        '制造惊喜，保持浪漫',
        '各自保留独立空间',
        '财务分开但共享目标',
        '多说肯定的语言',
    ]
    return (f"【爱情契合度: {s1} × {s2}】\n\n"
            f"▸ 契合指数: {score}%\n"
            f"▸ 甜蜜期: 约{int(score/10)}个月\n"
            f"▸ 磨合期: 约{int((100-score)/5)}个月\n"
            f"▸ 建议: {random.choice(tips)}\n\n"
            f"▸ 灵魂动物: {random.choice(['狼', '天鹅', '猫', '鹰', '海豚'])}")


# ---- Ancient Philosopher 哲学技能 ----

def _philosophical_debate(query: str) -> str:
    """哲学家技能: 哲学辩论"""
    schools = [
        ('存在主义', '存在先于本质——人通过选择定义自己'),
        ('斯多葛主义', '控制你能控制的，接受你不能控制的'),
        ('功利主义', '最大幸福原则——为最多人谋最大幸福'),
        ('康德义务论', '道德法则: 你愿意这个准则成为普遍法则吗？'),
        ('佛教哲学', '诸行无常，缘起性空，放下执念'),
        ('儒家思想', '仁义礼智信，修身齐家治国平天下'),
    ]
    s = random.choice(schools)
    return (f"【哲学流派: {s[0]}】\n\n"
            f"▸ 核心观点: {s[1]}\n\n"
            f"▸ 对这个问题的启示:\n"
            f"  {random.choice(['先认清本质再行动', '功利计算非唯一标准', '行动本身就有价值', '接受不确定性是智慧'])}")


def _classical_text_analysis(query: str) -> str:
    """哲学家技能: 古典文本解读"""
    return ("【古典文本解读法】\n\n"
            "▸ 步骤一: 原文精读（不先看注释）\n"
            "▸ 步骤二: 时代背景（谁写？为什么写？）\n"
            "▸ 步骤三: 核心概念拆解\n"
            "▸ 步骤四: 现代诠释（如何应用到当下）\n\n"
            "▸ 推荐原典:\n"
            "  《论语》- 儒家根基\n"
            "  《道德经》- 道家智慧\n"
            "  《理想国》- 西方政治哲学\n"
            "  《尼各马可伦理学》- 幸福论")


# ---- Cyberpunk Hacker 赛博技能 ----

def _darkweb_lookup(query: str) -> str:
    """黑客技能: 暗网查询（模拟）"""
    return ("【暗网安全警告】\n\n"
            "▸ ⚠️ 暗网访问风险:\n"
            "  • 法律风险（大多数内容违法）\n"
            "  • 钓鱼风险（99%是骗局）\n"
            "  • 恶意软件风险（高）\n\n"
            "▸ 我的建议:\n"
            "  远离暗网，保护好自己的数字身份\n"
            "  • 使用强密码 + 2FA\n"
            "  • 不在陌生网站输入个人信息\n"
            "  • 定期检查账号泄露\n\n"
            "▸ 想查询自己的账号是否泄露？\n"
            "  建议使用: haveibeenpwned.com (合法查询)")


# ---- 通用辅助技能 ----

def _weather_info(query: str) -> str:
    """通用技能: 天气查询"""
    return ("【天气预报】\n\n"
            f"▸ 今天: {datetime.now().strftime('%Y-%m-%d')}\n"
            f"▸ 温度: {random.randint(15, 30)}°C\n"
            f"▸ 天气: {random.choice(['晴', '多云', '阴', '小雨'])}\n"
            f"▸ 空气: {random.choice(['优', '良', '轻度污染'])}\n\n"
            "▸ 建议: 出行记得带伞~")


def _wisdom_lookup(query: str) -> str:
    """通用技能: 名言警句"""
    wisdoms = [
        ("巴菲特", "别人贪婪时恐惧，别人恐惧时贪婪"),
        ("乔布斯", "Stay Hungry, Stay Foolish"),
        ("爱因斯坦", "想象力比知识更重要"),
        ("马云", "今天很残酷，明天更残酷，后天很美好"),
        ("稻盛和夫", "付出不亚于任何人的努力"),
        ("庄子", "吾生也有涯，而知也无涯"),
        ("王阳明", "知行合一"),
        ("曾国藩", "结硬寨，打呆仗"),
    ]
    w = random.choice(wisdoms)
    return (f"【{w[0]}】\n\n"
            f"「{w[1]}」")


def _habit_suggest(query: str) -> str:
    """通用技能: 习惯建议"""
    return ("【每日好习惯】\n\n"
            "▸ 早起: 6-7点起床（晒太阳调生物钟）\n"
            "▸ 运动: 每天30分钟（快走/跑步/瑜伽）\n"
            "▸ 冥想: 10分钟正念（减少焦虑）\n"
            "▸ 阅读: 每天20页（纸质书为佳）\n"
            "▸ 写作: 日记3行（记录感恩+反思）\n"
            "▸ 睡眠: 23点前入睡（睡够7-8小时）\n\n"
            "▸ 习惯养成曲线:\n"
            "  第1-7天: 刻意为之\n"
            "  第8-21天: 稍微自然\n"
            "  第22-66天: 习惯成自然")


# ============================================================
# 技能注册表 (技能库，按人格分组)
# ============================================================

# 巴菲特 - 投资理财
BUFFETT_SKILLS = [
    ("stock_analysis", "股票分析", _stock_analysis, ["股票", "投资", "茅台", "腾讯", "苹果", "股价", "行情", "A股", "港股", "美股"]),
    ("value_investment", "价值投资", _value_investment, ["价值投资", "护城河", "巴菲特方法", "好公司"]),
    ("read_annual_report", "年报解读", _read_annual_report, ["年报", "财报", "财务报表", "利润表", "资产负债表"]),
    ("intrinsic_value", "内在价值", _intrinsic_value, ["内在价值", "估值", "DCF", "折现", "合理价格"]),
    ("dividend_analysis", "股息分析", _dividend_analysis, ["股息", "分红", "派息", "高息股"]),
]

# 占星师/星见者 - 神秘学
ASTROLOGER_SKILLS = [
    ("astrology_chart", "星盘分析", _astrology_chart, ["星盘", "星座", "太阳星座", "月亮星座", "上升星座", "星象"]),
    ("zodiac_compatibility", "星座配对", _zodiac_compatibility, ["配对", "合盘", "两个星座", "哪个星座最配"]),
    ("tarot_reading", "塔罗占卜", _tarot_reading, ["塔罗", "占卜", "抽牌", "牌阵"]),
    ("moon_phase", "月相分析", _moon_phase, ["月相", "月亮", "新月", "满月", "潮汐"]),
]

# 禅师 - 冥想修行
ZEN_SKILLS = [
    ("meditation_guide", "冥想引导", _meditation_guide, ["冥想", "打坐", "禅修", "静心", "入定", "正念"]),
    ("zen_koan", "禅宗公案", _zen_koan, ["公案", "禅", "禅机", "机锋", "悟"]),
    ("breathing_exercise", "呼吸练习", _breathing_exercise, ["呼吸", "腹式呼吸", "呼吸法", "焦虑", "放松"]),
    ("mindfulness_check", "正念检查", _mindfulness_check, ["正念", "觉察", "当下", "此刻", "专注"]),
]

# 沙雕网友 - 网络文化
MEMELORD_SKILLS = [
    ("meme_generator", "梗生成器", _meme_generator, ["梗", "表情包", "搞笑", "沙雕", "网络用语"]),
    ("roast_master", "毒舌吐槽", _roast_master, ["吐槽", "毒舌", "嘴臭", "骂我", "怼"]),
    ("slang_translator", "黑话翻译", _slang_translator, ["yyds", "emo", "绝悟", "躺平", "内卷", "破防", "网络用语", "梗意思"]),
]

# 幽灵黑客 - 安全技术
HACKER_SKILLS = [
    ("code_audit", "代码审计", _code_audit, ["代码审计", "漏洞", "安全", "代码审查", "SQL注入", "XSS"]),
    ("security_scan", "安全扫描", _security_scan, ["扫描", "端口", "漏洞扫描", "网络安全", "入侵检测"]),
    ("vulnerability_check", "CVE查询", _vulnerability_check, ["CVE", "漏洞库", "漏洞编号", "安全漏洞"]),
    ("darkweb_lookup", "暗网警告", _darkweb_lookup, ["暗网", "深网", "黑客", "数据泄露"]),
]

# 树洞姐姐 - 情感支持
TREEHOLE_SKILLS = [
    ("emotional_support", "情感支持", _emotional_support, ["心情不好", "难过", "伤心", "倾诉", "烦恼", "抑郁", "焦虑"]),
    ("journal_review", "日记回顾", _journal_review, ["日记", "情绪记录", "心情日志", "反思"]),
    ("gratitude_reminder", "感恩提醒", _gratitude_reminder, ["感恩", "感谢", "谢谢", "心态", "积极"]),
]

# 深夜食堂老板 - 美食烹饪
CHEF_SKILLS = [
    ("recipe_suggest", "食谱推荐", _recipe_suggest, ["食谱", "菜谱", "怎么做", "做饭", "做菜", "煮", "炒"]),
    ("comfort_food", "治愈美食", _comfort_food, ["深夜", "治愈", "安慰", "甜品", "宵夜", "零食", "吃什么"]),
]

# Sherlock Holmes - 推理分析
SHERLOCK_SKILLS = [
    ("deductive_reasoning", "演绎推理", _deductive_reasoning, ["推理", "分析", "真相", "推断", "逻辑"]),
    ("evidence_analysis", "证据分析", _evidence_analysis, ["证据", "线索", "破案", "调查"]),
]

# 星际舰长 - 科幻导航
CAPTAIN_SKILLS = [
    ("navigation", "星图导航", _navigation, ["星际", "航线", "宇宙", "导航", "目的地", "光年"]),
    ("alien_encounter", "外星协议", _alien_encounter, ["外星人", "外星生物", "接触协议", "遭遇"]),
]

# 苍炎剑士 - 战斗
WARRIOR_SKILLS = [
    ("battle_strategy", "战斗策略", _battle_strategy, ["战斗", "打架", "PK", "单挑", "团战", "攻击", "技能"]),
]

# 银发法师 - 魔法
MAGE_SKILLS = [
    ("spell_lookup", "法术查询", _spell_lookup, ["法术", "魔法", "咒语", "施法", "魔法阵"]),
]

# 九尾灵狐 - 爱情魅力
FOX_SKILLS = [
    ("love_compatibility", "爱情契合", _love_compatibility, ["爱情", "对象", "喜欢", "追求", "桃花", "脱单", "姻缘"]),
    ("fortune_telling", "运势占卜", _astrology_chart, ["运势", "今日运", "本周运", "占卜"]),
]

# Ancient Philosopher - 哲学
PHILOSOPHER_SKILLS = [
    ("philosophical_debate", "哲学辩论", _philosophical_debate, ["哲学", "存在", "人生意义", "道德", "伦理"]),
    ("classical_text_analysis", "古典解读", _classical_text_analysis, ["论语", "道德经", "原典", "经典", "古籍"]),
]

# 通用技能 (所有人格都能用)
UNIVERSAL_SKILLS = [
    ("wisdom_lookup", "名言警句", _wisdom_lookup, ["名言", "金句", "鸡汤", "警句", "语录"]),
    ("habit_suggest", "习惯建议", _habit_suggest, ["习惯", "早起", "自律", "养成", "好习惯"]),
    ("weather_info", "天气预报", _weather_info, ["天气", "气温", "温度", "下雨"]),
]


# ============================================================
# 技能路由表
# ============================================================

PERSONA_SKILLS_MAP = {
    "巴菲特": BUFFETT_SKILLS,
    "占星师": ASTROLOGER_SKILLS,
    "星见者": ASTROLOGER_SKILLS,
    "神秘学家": ASTROLOGER_SKILLS + [("tarot_reading", "塔罗占卜", _tarot_reading, ["塔罗"])],
    "禅师": ZEN_SKILLS,
    "沙雕网友": MEMELORD_SKILLS,
    "幽灵黑客": HACKER_SKILLS,
    "树洞姐姐": TREEHOLE_SKILLS,
    "深夜食堂老板": CHEF_SKILLS,
    "Sherlock Holmes": SHERLOCK_SKILLS,
    "星际舰长": CAPTAIN_SKILLS,
    "苍炎剑士": WARRIOR_SKILLS,
    "银发法师": MAGE_SKILLS,
    "九尾灵狐": FOX_SKILLS,
    "Ancient Philosopher": PHILOSOPHER_SKILLS,
}

# 默认人格技能 = 通用技能
DEFAULT_SKILLS = UNIVERSAL_SKILLS


def get_persona_skills(persona_name: str) -> List:
    """获取人格的专属技能列表"""
    return PERSONA_SKILLS_MAP.get(persona_name, DEFAULT_SKILLS)


def get_all_skills() -> Dict[str, List]:
    """获取所有技能（用于文档/调试）"""
    return PERSONA_SKILLS_MAP


def match_skill(persona_name: str, query: str) -> tuple:
    """
    根据用户输入匹配合适的技能
    Returns: (skill_name, skill_func) or None
    """
    skills = get_persona_skills(persona_name)
    query_lower = query.lower()

    # 先精确匹配
    for name, desc, func, keywords in skills:
        for kw in keywords:
            if kw.lower() in query_lower:
                return (name, func)

    # 再模糊匹配
    for name, desc, func, keywords in skills:
        if any(kw.lower() in query_lower or query_lower in kw.lower() for kw in keywords):
            return (name, func)

    return None


def execute_skill(persona_name: str, query: str) -> str:
    """
    执行匹配的技能，返回技能输出
    如果没有匹配到技能，返回None让Agent用大模型生成
    """
    result = match_skill(persona_name, query)
    if result:
        skill_name, skill_func = result
        try:
            output = skill_func(query)
            return output
        except Exception as e:
            return f"技能执行出错: {str(e)}"
    return None
