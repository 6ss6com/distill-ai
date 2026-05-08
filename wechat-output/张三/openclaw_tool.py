"""
OpenClaw Tool - 张三

从微信聊天记录蒸馏的AI人格技能。
Source: WeChat chat persona distiller
"""

TOOL_NAME = "wechat_persona_张三"
TOOL_DESCRIPTION = """张三 - 从微信聊天记录蒸馏的AI人格。

风格: 轻松随意
领域: 投资理财, 生活日常, 工作职场
口头禅: 的东西, 意思, 资的
"""


def invoke(message: str, user_id: str = "wechat_user") -> str:
    """
    调用人格进行对话

    注意: 此为Skill入口，实际调用需要DistillAI后端支持。
    或者直接使用预设的对话逻辑。
    """
    # 简单响应逻辑 (实际生产应连接DistillAI Agent)
    catchphrases = ["的东西", "意思", "资的", "真好啊", "投资的"]

    responses = ["今天天气真好啊", "我刚看完一本书 讲投资的", "《穷爸爸富爸爸》", "里面有个观点很有意思", "资产就是能把钱放进你口袋的东西"]

    # 关键词匹配简单回复
    keywords = {
        "投资": ["理财要谨慎啊", "我也在关注"],
        "股票": ["最近行情一般", "看好长期"],
        "开心": ["哈哈是啊", "开心最重要"],
        "难过": ["怎么了？", "说出来听听"],
        "吃饭": ["吃了啥", "我也饿了"],
    }

    for kw, reps in keywords.items():
        if kw in message:
            return reps[0]

    # 默认回复
    return "嗯，我懂你说的"


if __name__ == "__main__":
    print("=== 张三 Tool Test ===")
    print(invoke("今天很开心"))
    print(invoke("最近在关注股票"))
