"""
DistillAI - WeChat Chat Persona Distiller v2.0

从微信聊天记录中提取人格信息，打包成OpenClaw/Hermes技能。

支持格式:
1. WeChatMsg工具导出的SQLite (EnMicroMsg.db)
2. WeChat PC备份SQLite
3. 通用文本聊天记录 (TXT格式)
4. XML导出格式

用法:
    from wechat_distiller import WeChatDistiller
    distiller = WeChatDistiller()
    distiller.load_db(r"C:\WeChatMsg\WeChat.db")  # SQLite
    # 或
    distiller.load_txt(r"C:\聊天记录.txt")
    persona = distiller.distill(name="我的朋友")
    distiller.save_persona(persona, "my_friend.json")
    distiller.package_skill(persona, output_dir="output/")
"""

import re, json, sqlite3, os, hashlib, time
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from collections import Counter, defaultdict


# ============================================================
# 微信消息解析器
# ============================================================

class WeChatParser:
    """
    微信聊天记录解析器

    支持的表结构 (WeChatMsg / EnMicroMsg):
    - message: msgId, createTime, isSend, msgType, content, talker
    - chatroom: chatroomName, memberList
    - contact: username, nickname, type
    """

    def __init__(self):
        self.messages: List[Dict] = []
        self.contacts: Dict[str, Dict] = {}
        self.chatrooms: Dict[str, List[str]] = {}

    # ===== SQLite导入 =====
    def load_db(self, db_path: str, password: str = None) -> int:
        """
        从WeChat SQLite数据库加载聊天记录

        支持:
        - WeChatMsg导出的WeChat.db
        - EnMicroMsg.db (Android)
        - PC微信备份数据库

        Args:
            db_path: 数据库路径
            password: 可选，数据库密码(部分加密)
        """
        if not os.path.exists(db_path):
            raise FileNotFoundError(f"Database not found: {db_path}")

        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row

        # 尝试解密(如果需要)
        if password:
            try:
                conn.execute(f"PRAGMA key = '{password}'")
            except:
                pass

        cursor = conn.cursor()

        # 检测表结构
        tables = cursor.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        table_names = [t[0] for t in tables]

        # 找到消息表
        msg_table = None
        for candidate in ['message', 'MSG', 'ChatMessages', '(message)']:
            if candidate in table_names:
                msg_table = candidate
                break

        if msg_table is None:
            # 尝试自动检测
            for table in table_names:
                cols = [c[1] for c in cursor.execute(f"PRAGMA table_info({table})").fetchall()]
                if 'content' in cols and ('createTime' in cols or 'CreateTime' in cols):
                    msg_table = table
                    break

        if msg_table is None:
            raise ValueError(f"Cannot find message table. Tables: {table_names}")

        # 提取消息
        # 动态检测列名
        col_info = {c[1].lower(): c[1] for c in cursor.execute(f"PRAGMA table_info({msg_table})").fetchall()}
        time_col = col_info.get('createtime', col_info.get('create_time', 'createTime'))
        content_col = col_info.get('content', 'content')
        is_send_col = col_info.get('issend', col_info.get('is_send', 'isSend'))
        talker_col = col_info.get('talker', 'talker')
        msg_type_col = col_info.get('msgtype', col_info.get('msg_type', 'msgType'))

        rows = cursor.execute(f"""
            SELECT {time_col}, {content_col}, {is_send_col}, {talker_col}, {msg_type_col}
            FROM {msg_table}
            WHERE {content_col} IS NOT NULL AND {content_col} != ''
            ORDER BY {time_col}
        """).fetchall()

        self.messages = []
        for row in rows:
            create_time = row[0]
            content = row[1]
            is_send = row[2]  # 1=发送, 0=接收
            talker = row[3]
            msg_type = row[4]

            # 过滤: 只保留文本消息(type=1)
            if msg_type and int(msg_type) != 1:
                continue
            if not content or not isinstance(content, str):
                continue

            # 时间戳转换 (如果是毫秒级)
            if create_time and len(str(create_time)) > 13:
                create_time = int(create_time) // 1000
            elif create_time:
                create_time = int(create_time)

            self.messages.append({
                "content": content.strip(),
                "is_send": bool(is_send),
                "talker": talker or "unknown",
                "timestamp": create_time,
                "datetime": datetime.fromtimestamp(create_time).isoformat() if create_time else None,
            })

        # 提取联系人
        for table in ['contact', 'Contact', 'contact(contact)']:
            if table in table_names:
                try:
                    rows = cursor.execute(f"SELECT username, nickname, type FROM {table}").fetchall()
                    for row in rows:
                        self.contacts[row[0]] = {
                            "username": row[0],
                            "nickname": row[1] or row[0],
                            "type": row[2],
                        }
                except:
                    pass
                break

        # 提取群聊
        for table in ['chatroom', 'ChatRoom', 'chatroom(chatroom)']:
            if table in table_names:
                try:
                    rows = cursor.execute(f"SELECT chatroomname, memberlist FROM {table}").fetchall()
                    for row in rows:
                        self.chatrooms[row[0]] = str(row[1]).split("^G") if row[1] else []
                except:
                    pass
                break

        conn.close()
        return len(self.messages)

    # ===== TXT导入 =====
    def load_txt(self, txt_path: str, encoding: str = "utf-8") -> int:
        """
        从TXT文本聊天记录导入

        支持格式:
        - 逐行: "2024-01-01 12:00:00 | 张三: 你好"
        - 逐行: "[2024-01-01 12:00] 张三: 你好"
        - 逐行: "张三: 你好"
        - 分段: "=== 2024-01-01 ===" 开头的新段落
        """
        with open(txt_path, "r", encoding=encoding, errors="ignore") as f:
            lines = f.readlines()

        self.messages = []

        # 正则表达式
        patterns = [
            # "2024-01-01 12:00:00 | 张三: 你好"
            re.compile(r'^(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})\s*[|：:]\s*([^:：]+)[:：]\s*(.+)$'),
            # "[2024-01-01 12:00] 张三: 你好"
            re.compile(r'^\[(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2})\]\s*([^:：]+)[:：]\s*(.+)$'),
            # "张三: 你好" (无日期)
            re.compile(r'^([^:：\s]+)[:：]\s*(.+)$'),
        ]

        current_time = None
        current_sender = None

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # 检测日期分隔符
            date_match = re.match(r'^[=◆「【「]*\s*(\d{4}[-/]\d{2}[-/]\d{2})', line)
            if date_match:
                try:
                    current_time = datetime.strptime(date_match.group(1), "%Y-%m-%d")
                except:
                    try:
                        current_time = datetime.strptime(date_match.group(1), "%Y/%m/%d")
                    except:
                        pass
                continue

            # 尝试匹配消息模式
            for i, pattern in enumerate(patterns):
                m = pattern.match(line)
                if m:
                    if i == 2:  # 无日期模式，用之前的
                        sender = m.group(1).strip()
                        content = m.group(2).strip()
                    else:
                        if i == 0:
                            try:
                                current_time = datetime.strptime(m.group(1), "%Y-%m-%d %H:%M:%S")
                            except:
                                try:
                                    current_time = datetime.strptime(m.group(1), "%Y-%m-%d %H:%M")
                                except:
                                    pass
                        sender = m.group(2).strip()
                        content = m.group(3).strip()

                    if sender and content and len(content) < 5000:  # 过滤异常长消息
                        # 判断是否为自己的消息
                        is_send = sender in ["我", "Me", "我自己"]

                        self.messages.append({
                            "content": content,
                            "is_send": is_send,
                            "talker": sender,
                            "timestamp": int(current_time.timestamp()) if current_time else 0,
                            "datetime": current_time.isoformat() if current_time else None,
                        })
                        current_time = None  # 重置
                    break

        return len(self.messages)

    # ===== XML导入 (部分导出工具) =====
    def load_xml(self, xml_path: str) -> int:
        """从XML格式导入"""
        import xml.etree.ElementTree as ET

        with open(xml_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        self.messages = []

        # 尝试解析为XML
        try:
            root = ET.fromstring(content)
            for msg in root.findall(".//msg") + root.findall(".//message"):
                content_text = ""
                # 尝试多个可能的内容标签
                for tag in ['content', 'text', 'msgContent']:
                    t = msg.find(tag)
                    if t is not None and t.text:
                        content_text = t.text.strip()
                        break

                if not content_text:
                    continue

                # 提取发送者
                sender = None
                for tag in ['sender', 'from', 'username', 'nickname']:
                    s = msg.find(tag)
                    if s is not None and s.text:
                        sender = s.text.strip()
                        break

                # 提取时间
                timestamp = 0
                for tag in ['datetime', 'time', 'createTime', 'timestamp']:
                    t = msg.find(tag)
                    if t is not None and t.text:
                        try:
                            timestamp = int(t.text)
                            if timestamp > 1e12:  # 毫秒转秒
                                timestamp //= 1000
                            break
                        except:
                            pass

                if sender:
                    self.messages.append({
                        "content": content_text,
                        "is_send": False,
                        "talker": sender,
                        "timestamp": timestamp,
                        "datetime": datetime.fromtimestamp(timestamp).isoformat() if timestamp else None,
                    })
        except ET.ParseError:
            # 不是XML，当作文本处理
            pass

        return len(self.messages)

    # ===== 统计信息 =====
    def stats(self) -> dict:
        """返回统计信息"""
        if not self.messages:
            return {"total": 0}

        senders = Counter(m["talker"] for m in self.messages)
        total = len(self.messages)
        date_range = None
        if self.messages:
            times = [m["timestamp"] for m in self.messages if m["timestamp"]]
            if times:
                min_t = datetime.fromtimestamp(min(times))
                max_t = datetime.fromtimestamp(max(times))
                date_range = f"{min_t.strftime('%Y-%m-%d')} ~ {max_t.strftime('%Y-%m-%d')}"

        return {
            "total_messages": total,
            "unique_senders": len(senders),
            "top_senders": senders.most_common(5),
            "date_range": date_range,
            "avg_length": sum(len(m["content"]) for m in self.messages) // max(total, 1),
        }


# ============================================================
# 人格蒸馏器
# ============================================================

class PersonaDistiller:
    """
    从微信聊天记录中蒸馏人格

    分析维度:
    1. 词汇使用 (vocabulary)
    2. 句式风格 (sentence patterns)
    3. 情感倾向 (emotion)
    4. 话题偏好 (topics)
    5. 交互模式 (communication style)
    6. 口头禅/习惯 (catchphrases)
    7. 价值观/立场 (values)
    8. 决策风格 (decision patterns)
    """

    # 情感词库
    POSITIVE_WORDS = [
        '好', '棒', '赞', '厉害', '牛', '强', '喜欢', '爱', '开心', '快乐',
        '哈哈', '嘻嘻', '呵呵', '笑死', '太棒', '优秀', '完美', '感谢',
        '感恩', '幸福', '满足', '期待', '希望', '加油', '支持', '同意',
        '确实', '当然', '肯定', '没错', '可以', '行', '好的', '收到', '明白'
    ]

    NEGATIVE_WORDS = [
        '坏', '差', '烂', '讨厌', '恨', '难过', '伤心', '烦', '累', '困',
        '压力', '焦虑', '担心', '害怕', '生气', '失望', '无奈', '无语',
        '算了', '随便', '不管', '滚', '切', '哼', '悲哀', '痛苦', '崩溃',
        '傻', '笨', '烦人', '讨厌', '恶心', '受不了', '烦死了'
    ]

    # 网络用语词库
    SLANG_WORDS = [
        'yyds', '绝绝子', 'emo', '内卷', '躺平', '摆烂', '冲', '冲鸭',
        '芭比Q', '无语子', '芜湖', '夺笋', '凡尔赛', '社死', '破防',
        '绝悟', '赢麻', '蚌埠住', '老铁', '扎心', '真香', '奥利给',
        'gkd', 'u1s1', 'nbcs', 'xswl', 'zqsg', 'ssfd', 'plmm', 'plgg'
    ]

    # 句式特征
    QUESTION_PATTERNS = [
        (re.compile(r'^(怎么|如何|为什么|为何|什么|哪|谁|多少|几|是不是|有没有)\?'), 'question_wh'),
        (re.compile(r'^(吗|嘛|呀|吧|啊)\?'), 'question_yn'),
        (re.compile(r'^(帮我|给我|我想|我要|能不能|可以帮我)\?'), 'request'),
    ]

    def __init__(self):
        self.analysis = {}

    def analyze(self, messages: List[Dict], target_sender: str = None) -> dict:
        """
        分析聊天记录，提取人格特征

        Args:
            messages: 消息列表
            target_sender: 如果指定，只分析该发送者的消息
        """
        # 过滤目标发送者的消息
        if target_sender:
            msgs = [m for m in messages if m.get("talker") == target_sender]
        else:
            # 分析所有发送者，尝试找主要人格
            senders = Counter(m["talker"] for m in messages)
            if not senders:
                return {}
            target_sender = senders.most_common(1)[0][0]
            msgs = [m for m in messages if m.get("talker") == target_sender]

        if not msgs:
            return {}

        contents = [m["content"] for m in msgs]

        self.analysis = {
            "sender": target_sender,
            "total_messages": len(msgs),
            "vocabulary": self._analyze_vocabulary(contents),
            "emotion": self._analyze_emotion(contents),
            "topics": self._analyze_topics(contents),
            "sentence_patterns": self._analyze_sentences(contents),
            "catchphrases": self._extract_catchphrases(contents),
            "communication_style": self._analyze_style(contents),
            "values": self._analyze_values(contents),
            "decision_patterns": self._analyze_decision(contents),
            "interaction_style": self._analyze_interaction(msgs),
            "speech_samples": self._extract_samples(contents, n=10),
        }

        return self.analysis

    def _analyze_vocabulary(self, contents: List[str]) -> dict:
        """分析词汇使用"""
        all_text = "".join(contents)

        # 词频统计
        words = re.findall(r'[\u4e00-\u9fff]+', all_text)  # 中文词
        word_freq = Counter()
        for w in words:
            if len(w) >= 2:  # 至少2个字
                word_freq[w] += 1

        # 网络用语
        slang_count = sum(1 for s in self.SLANG_WORDS if s in all_text.lower())

        # 英文使用
        english_count = len(re.findall(r'[a-zA-Z]{3,}', all_text))

        # 表情符号
        emoji_count = len(re.findall(r'[\U0001F000-\U0001F9FF]', all_text))

        most_common = word_freq.most_common(20)

        return {
            "top_words": [{"word": w, "count": c} for w, c in most_common],
            "slang_usage": slang_count,
            "english_usage": english_count,
            "emoji_usage": emoji_count,
        }

    def _analyze_emotion(self, contents: List[str]) -> dict:
        """分析情感倾向"""
        all_text = "".join(contents)
        total_words = sum(len(c) for c in contents)

        positive_count = sum(all_text.count(w) for w in self.POSITIVE_WORDS)
        negative_count = sum(all_text.count(w) for w in self.NEGATIVE_WORDS)

        # 情绪词强度
        intense_positive = sum(1 for w in ['超', '巨', '太', '非常', '特别'] if w + '好' in all_text or w + '棒' in all_text)
        intense_negative = sum(1 for w in ['超', '巨', '太', '非常', '特别'] if w + '烦' in all_text or w + '讨厌' in all_text)

        net_sentiment = positive_count - negative_count
        sentiment_ratio = net_sentiment / max(len(contents), 1)

        if net_sentiment > 5:
            sentiment_label = "积极乐观"
        elif net_sentiment < -5:
            sentiment_label = "消极悲观"
        else:
            sentiment_label = "中性平淡"

        return {
            "sentiment": sentiment_label,
            "positive_score": positive_count,
            "negative_score": negative_count,
            "net_sentiment": net_sentiment,
            "sentiment_ratio": round(sentiment_ratio, 2),
            "intense_positive": intense_positive,
            "intense_negative": intense_negative,
        }

    def _analyze_topics(self, contents: List[str]) -> dict:
        """分析话题偏好"""
        topic_keywords = {
            "投资理财": ["股票", "基金", "投资", "赚钱", "理财", "钱", "买", "卖", "涨", "跌", "收益", "本金"],
            "工作职场": ["工作", "上班", "老板", "同事", "公司", "项目", "客户", "开会", "加班", "辞职"],
            "情感关系": ["男/女", "朋友", "家人", "对象", "分手", "喜欢", "爱", "吵架", "结婚", "单身"],
            "技术编程": ["代码", "编程", "Python", "Java", "程序员", "bug", "Git", "API", "数据库"],
            "生活日常": ["吃", "喝", "玩", "睡", "天气", "出门", "回家", "做饭", "吃饭"],
            "娱乐八卦": ["电影", "电视剧", "综艺", "游戏", "明星", "综艺", "八卦", "热搜", "抖音"],
            "健康运动": ["跑步", "健身", "减肥", "身体", "医院", "医生", "养生", "瑜伽"],
            "学习教育": ["学习", "考试", "读书", "学校", "课程", "培训", "考证", "英语"],
            "AI科技": ["AI", "人工智能", "ChatGPT", "GPT", "大模型", "科技", "未来", "智能"],
        }

        topic_scores = {}
        all_text = "".join(contents)

        for topic, keywords in topic_keywords.items():
            score = sum(all_text.count(kw) for kw in keywords)
            if score > 0:
                topic_scores[topic] = score

        # 排序
        top_topics = sorted(topic_scores.items(), key=lambda x: x[1], reverse=True)[:5]

        return {
            "top_topics": [{"topic": t, "score": s} for t, s in top_topics],
            "topic_distribution": topic_scores,
        }

    def _analyze_sentences(self, contents: List[str]) -> dict:
        """分析句式特征"""
        question_count = 0
        exclamation_count = 0
        ellipsis_count = 0
        short_msg_count = 0  # <10字

        for c in contents:
            # 问句
            if '?' in c or '？' in c:
                question_count += 1

            # 感叹句
            if '!' in c or '！' in c:
                exclamation_count += 1

            # 省略号
            if '…' in c or '...' in c:
                ellipsis_count += 1

            # 短消息
            if len(c) < 10:
                short_msg_count += 1

        total = max(len(contents), 1)

        # 平均长度
        avg_length = sum(len(c) for c in contents) // total

        # 句式偏好
        patterns = []
        if question_count / total > 0.2:
            patterns.append("爱提问")
        if exclamation_count / total > 0.1:
            patterns.append("爱感叹")
        if ellipsis_count / total > 0.05:
            patterns.append("话留半句")
        if short_msg_count / total > 0.5:
            patterns.append("简短直接")

        return {
            "avg_length": avg_length,
            "question_ratio": round(question_count / total, 2),
            "exclamation_ratio": round(exclamation_count / total, 2),
            "short_msg_ratio": round(short_msg_count / total, 2),
            "patterns": patterns,
        }

    def _extract_catchphrases(self, contents: List[str]) -> List[str]:
        """提取口头禅"""
        # 常见结尾模式
        endings = []
        for c in contents:
            c = c.strip()
            if len(c) > 3:
                endings.append(c[-3:])

        # 统计最常见的3字结尾
        end_freq = Counter(endings)
        catchphrases = [e for e, _ in end_freq.most_common(10) if len(e) >= 2][:5]

        # 额外: 常见语气词
        sentence_enders = [c.strip()[-2:] for c in contents if len(c.strip()) >= 2]
        ender_freq = Counter(sentence_enders)
        final_catch = [e for e, _ in ender_freq.most_common(10) if len(e) >= 2 and not any(c.isdigit() for c in e)][:5]

        return list(set(catchphrases + final_catch))[:8]

    def _analyze_style(self, contents: List[str]) -> dict:
        """分析沟通风格"""
        all_text = "".join(contents)

        # 正式程度
        formal_words = ["因此", "然而", "所以", "由于", "关于", "根据", "表明", "认为"]
        informal_words = ["哈哈", "嘿嘿", "嗯", "啊", "嘛", "啦", "呀", "呗"]

        formal_count = sum(all_text.count(w) for w in formal_words)
        informal_count = sum(all_text.count(w) for w in informal_words)

        if informal_count > formal_count * 2:
            tone = "轻松随意"
        elif formal_count > informal_count:
            tone = "正式严谨"
        else:
            tone = "适中切换"

        # 直接程度
        direct_words = ["我", "觉得", "要", "不要", "想", "认为", "就是"]
        indirect_words = ["可能", "也许", "大概", "不知道", "不太确定", "不好说"]

        direct_count = sum(all_text.count(w) for w in direct_words)
        indirect_count = sum(all_text.count(w) for w in indirect_words)

        directness = "直接" if direct_count > indirect_count else "委婉"

        # Emoji使用
        emoji_pattern = re.compile(r'[\U0001F000-\U0001F9FF]')
        emojis = emoji_pattern.findall(all_text)
        emoji_freq = Counter(emojis)
        top_emojis = [e for e, _ in emoji_freq.most_common(5)]

        return {
            "tone": tone,
            "directness": directness,
            "emoji_usage": len(emojis),
            "top_emojis": top_emojis,
        }

    def _analyze_values(self, contents: List[str]) -> dict:
        """分析价值观/立场"""
        all_text = "".join(contents)

        value_keywords = {
            "务实": ["实际", "有用", "赚钱", "现实", "实用", "效果", "结果"],
            "理想": ["梦想", "希望", "未来", "理想", "追求", "目标", "愿景"],
            "情感": ["感情", "家人", "朋友", "爱情", "亲情", "友情", "在乎"],
            "自由": ["自由", "独立", "自主", "随性", "不想被束缚", "自己开心"],
            "责任": ["应该", "责任", "义务", "担当", "成熟", "靠谱"],
            "享乐": ["享受", "舒服", "开心", "快乐", "好玩", "有趣", "爽"],
            "成就": ["成功", "优秀", "厉害", "赢", "第一", "最好", "变强"],
        }

        value_scores = {}
        for value, keywords in value_keywords.items():
            score = sum(all_text.count(kw) for kw in keywords)
            if score > 0:
                value_scores[value] = score

        top_values = sorted(value_scores.items(), key=lambda x: x[1], reverse=True)[:3]

        return {
            "top_values": [{"value": v, "score": s} for v, s in top_values],
        }

    def _analyze_decision(self, contents: List[str]) -> dict:
        """分析决策风格"""
        all_text = "".join(contents)

        decisive_words = ["就", "马上", "立刻", "定了", "决定", "必须", "一定"]
        cautious_words = ["考虑", "想想", "再说", "不急", "慢慢来", "慎重", "三思"]

        decisive_count = sum(all_text.count(w) for w in decisive_words)
        cautious_count = sum(all_text.count(w) for w in cautious_words)

        if decisive_count > cautious_count * 1.5:
            style = "果断快速"
        elif cautious_count > decisive_count:
            style = "谨慎稳重"
        else:
            style = "随机应变"

        # 风险偏好
        risk_words = ["试试", "赌一把", "冒险", "博", "冲", "搞", "干"]
        safe_words = ["稳妥", "保守", "安全", "保险", "稳", "确定"]

        risk_count = sum(all_text.count(w) for w in risk_words)
        safe_count = sum(all_text.count(w) for w in safe_words)

        if risk_count > safe_count:
            risk = "激进冒险"
        elif safe_count > risk_count:
            risk = "保守稳健"
        else:
            risk = "风险中性"

        return {
            "decision_style": style,
            "risk_preference": risk,
        }

    def _analyze_interaction(self, messages: List[Dict]) -> dict:
        """分析交互模式"""
        total = len(messages)
        send_count = sum(1 for m in messages if m.get("is_send"))
        recv_count = total - send_count

        # 回复速度 (通过消息间隔推断)
        timestamps = sorted([m["timestamp"] for m in messages if m.get("timestamp")])
        intervals = []
        for i in range(1, min(len(timestamps), 50)):  # 只看前50条
            diff = timestamps[i] - timestamps[i-1]
            if 0 < diff < 86400:  # 24小时内的间隔
                intervals.append(diff)

        avg_reply_min = sum(intervals) // max(len(intervals), 1) // 60 if intervals else 0

        return {
            "send_ratio": round(send_count / max(total, 1), 2),
            "recv_ratio": round(recv_count / max(total, 1), 2),
            "avg_reply_minutes": avg_reply_min,
            "participation": "主动" if send_count > recv_count else "被动",
        }

    def _extract_samples(self, contents: List[str], n: int = 10) -> List[str]:
        """提取典型发言样本"""
        # 选择有代表性的消息
        samples = []
        for c in contents:
            c = c.strip()
            if len(c) >= 5 and len(c) <= 200:
                samples.append(c)
        return samples[:n]


# ============================================================
# 人格卡片生成器
# ============================================================

class PersonaCardGenerator:
    """将分析结果生成DistillAI人格卡片"""

    def __init__(self):
        pass

    def generate(self, analysis: dict, name: str, avatar: str = "😊") -> dict:
        """
        生成DistillAI人格卡片
        """
        if not analysis:
            return {}

        emotion = analysis.get("emotion", {})
        topics = analysis.get("topics", {})
        style = analysis.get("communication_style", {})
        sentences = analysis.get("sentence_patterns", {})
        catchphrases = analysis.get("catchphrases", [])
        samples = analysis.get("speech_samples", [])
        decision = analysis.get("decision_patterns", {})
        values = analysis.get("values", {})

        # 根据分析推断沟通风格
        tone = style.get("tone", "随和")
        directness = style.get("directness", "直接")
        sentiment = emotion.get("sentiment", "中性")

        # 推断emoji风格
        emoji_usage = style.get("emoji_usage", 0)
        top_emojis = style.get("top_emojis", [])

        # 根据话题推断知识领域
        top_topics = topics.get("top_topics", [])
        knowledge_areas = [t["topic"] for t in top_topics[:3]]

        # 根据决策风格推断风险偏好
        risk = decision.get("risk_preference", "中性")
        decision_style = decision.get("decision_style", "随机应变")

        # 生成描述
        description = f"基于微信聊天记录蒸馏的AI人格，擅长{knowledge_areas[0] if knowledge_areas else '日常交流'}"

        # 生成thinking_prompt
        thinking_prompt = self._generate_thinking_prompt(analysis)

        # 生成edge_cases
        edge_cases = self._generate_edge_cases(analysis)

        card = {
            "avatar": avatar,
            "core_identity": {
                "name": name,
                "description": description,
            },
            "communication_style": {
                "tone": tone,
                "structure": "简短直接" if sentences.get("short_msg_ratio", 0) > 0.5 else "自然流畅",
                "vocabulary": "网络用语多" if analysis.get("vocabulary", {}).get("slang_usage", 0) > 5 else "日常用语",
                "emoji_usage": f"常用{','.join(top_emojis[:3])}" if top_emojis else "偶尔用",
                "sentence_length": "短句" if sentences.get("avg_length", 50) < 30 else "适中",
            },
            "decision_patterns": {
                "risk_tolerance": risk,
                "speed_vs_accuracy": "快" if decision_style == "果断快速" else "稳",
                "information_threshold": "80%足够" if decision_style == "果断快速" else "95%才出手",
            },
            "values": [v["value"] for v in values.get("top_values", [])] or ["务实", "开心就好"],
            "knowledge": knowledge_areas or ["日常闲聊"],
            "goals": ["开心聊天", "真诚交流"],
            "biases": ["有自己立场", "偶尔主观"],
            "speech_samples": samples[:5],
            "catchphrases": catchphrases[:5],
            "edge_cases": edge_cases,
            "thinking_prompt": thinking_prompt,
            "_meta": {
                "source": "wechat_chat",
                "generated_at": datetime.now().isoformat(),
                "message_count": analysis.get("total_messages", 0),
                "sentiment": sentiment,
                "confidence": self._calc_confidence(analysis),
            }
        }

        return card

    def _generate_thinking_prompt(self, analysis: dict) -> str:
        tone = analysis.get("communication_style", {}).get("tone", "")
        topics = [t["topic"] for t in analysis.get("topics", {}).get("top_topics", [])[:2]]
        risk = analysis.get("decision_patterns", {}).get("risk_preference", "")

        parts = []
        if topics:
            parts.append(f"这个话题涉及{topics[0]}，用相关知识回答")
        if "积极" in analysis.get("emotion", {}).get("sentiment", ""):
            parts.append("保持积极乐观的态度")
        elif "消极" in analysis.get("emotion", {}).get("sentiment", ""):
            parts.append("理解负面情绪，给出安慰")
        if risk:
            parts.append(f"决策风格: {risk}")
        if not parts:
            parts.append("像朋友聊天一样自然回应")

        return " | ".join(parts)

    def _generate_edge_cases(self, analysis: dict) -> List[str]:
        cases = []
        sentiment = analysis.get("emotion", {}).get("sentiment", "")

        if "消极" in sentiment:
            cases.append("被问为什么心情不好——可能会倾诉也可能不想说，尊重对方意愿")
        if analysis.get("vocabulary", {}).get("slang_usage", 0) > 5:
            cases.append("被问网络用语——可以解释但不刻意卖弄")
        if analysis.get("sentence_patterns", {}).get("short_msg_ratio", 0) > 0.5:
            cases.append("被说消息太短——我就是这个风格，不改")

        cases.append("被问AI身份——坦诚说是AI，但保持这个聊天风格")
        cases.append("遇到不懂的话题——直接说不懂，不会装懂")

        return cases[:5]

    def _calc_confidence(self, analysis: dict) -> float:
        """计算人格蒸馏的可信度"""
        score = 0.5
        if analysis.get("total_messages", 0) > 100:
            score += 0.1
        if analysis.get("total_messages", 0) > 500:
            score += 0.1
        if len(analysis.get("speech_samples", [])) >= 5:
            score += 0.1
        if analysis.get("topics", {}).get("top_topics"):
            score += 0.1
        return min(score, 0.95)


# ============================================================
# OpenClaw Skill打包器
# ============================================================

class SkillPackager:
    """
    将蒸馏的人格打包成OpenClaw/Hermes技能
    """

    def __init__(self):
        self.base_dir = Path.home() / ".openclaw" / "workspace" / "distill-ai" / "skills"

    def package_skill(self, persona: dict, output_dir: str = None) -> str:
        """
        打包成人格技能到指定目录

        生成文件:
        - SKILL.md
        - persona.json (人格卡片)
        - _meta.json (元数据)
        - openclaw_tool.py (工具入口)
        """
        name = persona.get("core_identity", {}).get("name", "unknown")
        slug = re.sub(r'[^\w-]', '', name.lower().replace(' ', '-'))

        if output_dir:
            skill_dir = Path(output_dir) / slug
        else:
            skill_dir = self.base_dir / slug

        skill_dir.mkdir(parents=True, exist_ok=True)

        # 1. persona.json
        persona_file = skill_dir / "persona.json"
        with open(persona_file, "w", encoding="utf-8") as f:
            json.dump(persona, f, ensure_ascii=False, indent=2)

        # 2. SKILL.md
        skill_md = self._generate_skill_md(persona, slug)
        with open(skill_dir / "SKILL.md", "w", encoding="utf-8") as f:
            f.write(skill_md)

        # 3. _meta.json
        meta = {
            "ownerId": "distillai",
            "slug": slug,
            "version": "1.0.0",
            "publishedAt": int(time.time() * 1000),
            "tags": ["persona", "wechat-distilled", "custom"],
            "source": "wechat-chat-distilled",
            "generatedAt": datetime.now().isoformat(),
            "compatibility": ">=2.0.0"
        }
        with open(skill_dir / "_meta.json", "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)

        # 4. openclaw_tool.py
        tool_py = self._generate_tool_py(persona, slug)
        with open(skill_dir / "openclaw_tool.py", "w", encoding="utf-8") as f:
            f.write(tool_py)

        return str(skill_dir)

    def _generate_skill_md(self, persona: dict, slug: str) -> str:
        name = persona.get("core_identity", {}).get("name", "")
        description = persona.get("core_identity", {}).get("description", "")
        tone = persona.get("communication_style", {}).get("tone", "")
        knowledge = persona.get("knowledge", [])
        catchphrases = persona.get("catchphrases", [])
        samples = persona.get("speech_samples", [])[:3]

        knowledge_str = "、".join(knowledge[:5]) if knowledge else "日常闲聊"

        md = f"""---
name: {name}
slug: {slug}
version: 1.0.0
homepage: https://github.com/6ss6com/distill-ai
description: 从微信聊天记录蒸馏的AI人格 - {description}
changelog: |
  v1.0 - 初始版本 (从WeChat聊天记录蒸馏)
metadata: {{"openclaw":{{"emoji":"{persona.get('avatar', '🤖')}","category":"persona","os":["linux","darwin","win32"]}}}}
---

## {name}

**风格**: {tone} | **领域**: {knowledge_str}

### 简介

{description}

### 沟通风格

- **语气**: {persona.get('communication_style', {}).get('tone', '')}
- **句长**: {persona.get('communication_style', {}).get('sentence_length', '')}
- **emoji**: {persona.get('communication_style', {}).get('emoji_usage', '')}

### 价值观

{', '.join(persona.get('values', [])) or '务实、开心就好'}

### 决策风格

- 风险偏好: {persona.get('decision_patterns', {}).get('risk_tolerance', '')}
- 决策速度: {persona.get('decision_patterns', {}).get('speed_vs_accuracy', '')}

### 口头禅

{', '.join(catchphrases[:5]) if catchphrases else '暂无明显口头禅'}

### 典型发言

"""
        for s in samples:
            md += f"> {s}\n\n"

        md += f"""
### 注意事项

"""
        for case in persona.get("edge_cases", []):
            md += f"- {case}\n"

        md += f"""
### 来源信息

- 源类型: WeChat聊天记录
- 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}
- 消息数量: {persona.get('_meta', {}).get('message_count', 'N/A')}
- 置信度: {persona.get('_meta', {}).get('confidence', 'N/A')}

### 调用方式

在OpenClaw中直接用`/chat {name} [消息]`或通过`distillai_persona`工具调用。
"""
        return md

    def _generate_tool_py(self, persona: dict, slug: str) -> str:
        name = persona.get("core_identity", {}).get("name", "")
        catchphrases = json.dumps(persona.get("catchphrases", [])[:5], ensure_ascii=False)
        samples = json.dumps(persona.get("speech_samples", [])[:5], ensure_ascii=False)
        thinking_prompt = persona.get("thinking_prompt", "").replace('"', '\\"')

        return f'''"""
OpenClaw Tool - {name}

从微信聊天记录蒸馏的AI人格技能。
Source: WeChat chat persona distiller
"""

TOOL_NAME = "wechat_persona_{slug}"
TOOL_DESCRIPTION = """{name} - 从微信聊天记录蒸馏的AI人格。

风格: {persona.get("communication_style", {}).get("tone", "")}
领域: {", ".join(persona.get("knowledge", [])[:3])}
口头禅: {", ".join(persona.get("catchphrases", [])[:3])}
"""


def invoke(message: str, user_id: str = "wechat_user") -> str:
    """
    调用人格进行对话

    注意: 此为Skill入口，实际调用需要DistillAI后端支持。
    或者直接使用预设的对话逻辑。
    """
    # 简单响应逻辑 (实际生产应连接DistillAI Agent)
    catchphrases = {catchphrases}

    responses = {samples}

    # 关键词匹配简单回复
    keywords = {{
        "投资": ["理财要谨慎啊", "我也在关注"],
        "股票": ["最近行情一般", "看好长期"],
        "开心": ["哈哈是啊", "开心最重要"],
        "难过": ["怎么了？", "说出来听听"],
        "吃饭": ["吃了啥", "我也饿了"],
    }}

    for kw, reps in keywords.items():
        if kw in message:
            return reps[0]

    # 默认回复
    return "嗯，我懂你说的"


if __name__ == "__main__":
    print("=== {name} Tool Test ===")
    print(invoke("今天很开心"))
    print(invoke("最近在关注股票"))
'''
