"""
DistillAI Universal Persona Distiller

Multi-source input persona distillation.

Supported sources:
1. WeChat    - .db/.txt/.xml
2. Telegram  - .json/.html/.txt
3. Discord   - .json/.txt
4. WhatsApp  - .txt/.json
5. QQ        - .db/.txt/.json
6. Signal    - .json/.txt
7. Email     - .mbox/.eml/.csv/.json
8. Books     - .txt/.md/.html
9. Twitter/X - .json/.csv/.txt
10. RSS      - .xml/.json
11. Slack    - .json
12. Notes    - .md/.json
13. Forums   - .html/.json/.txt
14. Custom   - .txt/.json/.log

Usage:
    from universal_distiller import auto_parse, PersonaDistiller
    from wechat_distiller import PersonaCardGenerator, SkillPackager

    # 1. Parse any supported source
    messages = auto_parse("path/to/chat.txt")

    # 2. Distill personality
    from wechat_distiller import PersonaDistiller
    distiller = PersonaDistiller()
    analysis = distiller.analyze(messages, target_sender="张三")

    # 3. Generate persona card
    from wechat_distiller import PersonaCardGenerator
    gen = PersonaCardGenerator()
    persona = gen.generate(analysis, name="张三", avatar="😊")

    # 4. Package as OpenClaw skill
    from wechat_distiller import SkillPackager
    packager = SkillPackager()
    skill_dir = packager.package_skill(persona)
"""

import re, json, sqlite3, os, html, time
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from collections import Counter, defaultdict
from abc import ABC, abstractmethod


# ============================================================
# Base Parser Interface
# ============================================================

class BaseParser(ABC):
    name = "base"
    extensions = []

    @abstractmethod
    def parse(self, source: str) -> List[Dict]:
        pass

    def normalize_message(self, content: str, sender: str = None, timestamp: int = None, is_send: bool = None) -> Dict:
        return {
            "content": content.strip() if content else "",
            "sender": sender or "unknown",
            "timestamp": timestamp or 0,
            "is_send": bool(is_send),
            "source": self.name,
        }


# ============================================================
# WeChat Parser
# ============================================================

class WeChatParser(BaseParser):
    name = "wechat"
    extensions = [".db", ".txt", ".xml"]

    def parse(self, source: str) -> List[Dict]:
        ext = Path(source).suffix.lower()
        if ext == ".db":
            return self._parse_sqlite(source)
        elif ext == ".xml":
            return self._parse_xml(source)
        else:
            return self._parse_txt(source)

    def _parse_sqlite(self, db_path: str) -> List[Dict]:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        tables = [t[0] for t in cursor.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
        msg_table = None
        for t in tables:
            cols = [c[1].lower() for c in cursor.execute(f"PRAGMA table_info({t})").fetchall()]
            if 'content' in cols and ('createtime' in cols or 'create_time' in cols):
                msg_table = t
                break
        if not msg_table:
            conn.close()
            return []
        col_map = {c[1].lower(): c[1] for c in cursor.execute(f"PRAGMA table_info({msg_table})").fetchall()}
        tc = col_map.get('createtime', col_map.get('create_time', 'createTime'))
        cc = col_map.get('content', 'content')
        ic = col_map.get('issend', col_map.get('is_send', 'isSend'))
        mc = col_map.get('msgtype', col_map.get('msg_type', 'msgType'))
        rows = cursor.execute(f"SELECT {tc}, {cc}, {ic}, {mc} FROM {msg_table} WHERE {cc} IS NOT NULL AND {cc} != '' AND {mc} = 1").fetchall()
        messages = []
        for row in rows:
            ts = int(row[0]) // 1000 if len(str(row[0])) > 13 else int(row[0] or 0)
            if row[1] and isinstance(row[1], str):
                messages.append(self.normalize_message(content=row[1], timestamp=ts, is_send=bool(row[2])))
        conn.close()
        return messages

    def _parse_txt(self, path: str) -> List[Dict]:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        messages = []
        p1 = re.compile(r'^(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}(?::\d{2})?)\s*[|:]\s*([^:：]+)[:：]\s*(.+)$', re.M)
        for m in p1.finditer(content):
            try:
                ts = int(datetime.strptime(m.group(1), "%Y-%m-%d %H:%M:%S").timestamp())
            except:
                ts = 0
            messages.append(self.normalize_message(content=m.group(3).strip(), sender=m.group(2).strip(), timestamp=ts, is_send=m.group(2).strip() in ["我", "Me", "Myself"]))
        if not messages:
            p2 = re.compile(r'^([^:：\s]+)[:：]\s*(.+)$', re.M)
            for m in p2.finditer(content):
                s, t = m.group(1).strip(), m.group(2).strip()
                if len(t) < 5000 and len(s) < 50:
                    messages.append(self.normalize_message(content=t, sender=s, timestamp=0, is_send=s in ["我", "Me"]))
        return messages

    def _parse_xml(self, path: str) -> List[Dict]:
        import xml.etree.ElementTree as ET
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        messages = []
        try:
            root = ET.fromstring(content)
            for msg in root.findall(".//msg") + root.findall(".//message"):
                text = None
                for tag in ['content', 'text']:
                    t = msg.find(tag)
                    if t is not None and t.text:
                        text = t.text.strip()
                        break
                if not text:
                    continue
                sender = None
                for tag in ['sender', 'from']:
                    s = msg.find(tag)
                    if s is not None and s.text:
                        sender = s.text.strip()
                        break
                if sender:
                    messages.append(self.normalize_message(content=text, sender=sender))
        except ET.ParseError:
            pass
        return messages


# ============================================================
# Telegram Parser
# ============================================================

class TelegramParser(BaseParser):
    name = "telegram"
    extensions = [".json", ".html", ".txt"]

    def parse(self, source: str) -> List[Dict]:
        ext = Path(source).suffix.lower()
        if ext == ".json":
            return self._parse_json(source)
        elif ext == ".html":
            return self._parse_html(source)
        return self._parse_txt(source)

    def _parse_json(self, path: str) -> List[Dict]:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            data = json.load(f)
        messages = []
        msg_list = data if isinstance(data, list) else data.get("messages", [])
        for msg in msg_list:
            if not msg.get("text"):
                continue
            text = msg["text"]
            if isinstance(text, list):
                text = "".join(t.get("text", t) if isinstance(t, dict) else str(t) for t in text)
            messages.append(self.normalize_message(content=text, sender=msg.get("from", ""), timestamp=int(msg.get("date_unixtime", 0))))
        return messages

    def _parse_html(self, path: str) -> List[Dict]:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        messages = []
        pattern = re.compile(r'<span class="from-name"[^>]*>([^<]+)</span>.*?<div class="text"[^>]*>(.*?)</div>', re.S)
        for m in pattern.finditer(content):
            messages.append(self.normalize_message(content=html.unescape(m.group(2).strip()), sender=html.unescape(m.group(1).strip())))
        return messages

    def _parse_txt(self, path: str) -> List[Dict]:
        return WeChatParser()._parse_txt(path)


# ============================================================
# Discord Parser
# ============================================================

class DiscordParser(BaseParser):
    name = "discord"
    extensions = [".json", ".txt"]

    def parse(self, source: str) -> List[Dict]:
        if source.endswith(".json"):
            return self._parse_json(source)
        return self._parse_txt(source)

    def _parse_json(self, path: str) -> List[Dict]:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            data = json.load(f)
        messages = []
        channels = data if isinstance(data, list) else data.get("channels", [])
        if not isinstance(channels, list):
            channels = [channels]
        for ch in channels:
            for msg in ch.get("messages", []):
                if not msg.get("content"):
                    continue
                ts = msg.get("timestamp", 0)
                if isinstance(ts, str):
                    try:
                        ts = int(datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp())
                    except:
                        ts = 0
                messages.append(self.normalize_message(content=msg["content"], sender=msg.get("author", {}).get("name", "unknown"), timestamp=ts))
        return messages

    def _parse_txt(self, path: str) -> List[Dict]:
        return WeChatParser()._parse_txt(path)


# ============================================================
# WhatsApp Parser
# ============================================================

class WhatsAppParser(BaseParser):
    name = "whatsapp"
    extensions = [".txt", ".json"]

    def parse(self, source: str) -> List[Dict]:
        if source.endswith(".json"):
            return self._parse_json(source)
        return self._parse_txt(source)

    def _parse_txt(self, path: str) -> List[Dict]:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        messages = []
        pattern = re.compile(r'^(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2})\s*-\s*([^:]+):\s*(.+)$', re.M)
        for m in pattern.finditer(content):
            try:
                ts = int(datetime.strptime(m.group(1), "%Y-%m-%d %H:%M").timestamp())
            except:
                ts = 0
            messages.append(self.normalize_message(content=m.group(3).strip(), sender=m.group(2).strip(), timestamp=ts))
        return messages

    def _parse_json(self, path: str) -> List[Dict]:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        messages = []
        for msg in (data if isinstance(data, list) else data.get("messages", [])):
            if msg.get("text"):
                messages.append(self.normalize_message(content=msg["text"], sender=msg.get("sender_name", "unknown"), timestamp=int(msg.get("timestamp", 0) or 0), is_send=msg.get("is_sent_by_me", False)))
        return messages


# ============================================================
# Email Parser
# ============================================================

class EmailParser(BaseParser):
    name = "email"
    extensions = [".mbox", ".eml", ".csv", ".json"]

    def parse(self, source: str) -> List[Dict]:
        ext = Path(source).suffix.lower()
        if ext == ".json":
            return self._parse_csv_json(source)
        elif ext == ".csv":
            return self._parse_csv(source)
        else:
            return self._parse_mbox(source)

    def _parse_csv(self, path: str) -> List[Dict]:
        messages = []
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
        for line in lines[1:]:
            parts = line.split(",", 4)
            if len(parts) >= 4:
                sender = parts[0].strip().strip('"')
                subject = parts[2].strip().strip('"')
                body = parts[3].strip().strip('"')
                combined = f"{subject} {body}".strip()
                if combined:
                    messages.append(self.normalize_message(content=combined, sender=sender))
        return messages

    def _parse_csv_json(self, path: str) -> List[Dict]:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        messages = []
        for email in (data if isinstance(data, list) else [data]):
            body = email.get("body", "") or email.get("text", "") or ""
            subject = email.get("subject", "") or ""
            if body or subject:
                messages.append(self.normalize_message(content=f"{subject} {body}".strip(), sender=email.get("from", "unknown"), timestamp=int(email.get("timestamp", 0) or 0)))
        return messages

    def _parse_mbox(self, path: str) -> List[Dict]:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        messages = []
        parts = re.split(r'\nFrom ', content)
        for part in parts[1:101]:
            lines = part.split('\n')
            sender = "unknown"
            body_start = 0
            subject = ""
            for i, line in enumerate(lines):
                if line.startswith("From:"):
                    sender = re.sub(r'^[^<]*<([^>]+)>.*$', r'\1', line).strip() or sender
                elif line.startswith("Subject:"):
                    subject = line[8:].strip()
                elif line.strip() == "" and i > 3:
                    body_start = i + 1
                    break
            body = "\n".join(lines[body_start:body_start+50]).strip()
            combined = f"{subject} {body}".strip()[:2000]
            if combined:
                messages.append(self.normalize_message(content=combined, sender=sender))
        return messages


# ============================================================
# Book/Article Parser
# ============================================================

class BookParser(BaseParser):
    name = "book"
    extensions = [".txt", ".md", ".markdown", ".html"]

    def parse(self, source: str) -> List[Dict]:
        ext = Path(source).suffix.lower()
        if ext == ".html":
            return self._parse_html(source)
        return self._parse_txt(source, chunk_size=500)

    def _parse_txt(self, path: str, chunk_size: int = 300) -> List[Dict]:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        content = re.sub(r'\r\n', '\n', content)
        content = re.sub(r'\n{3,}', '\n\n', content)
        chapters = re.split(r'(?=^#{1,3}\s+\w)', content, flags=re.M)
        if len(chapters) < 3:
            chapters = [content[i:i+chunk_size] for i in range(0, len(content), chunk_size)]
        messages = []
        for chunk in chapters:
            chunk = chunk.strip()
            if len(chunk) >= 50:
                messages.append(self.normalize_message(content=chunk, sender="author", is_send=True))
        return messages

    def _parse_html(self, path: str) -> List[Dict]:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        content = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.S | re.I)
        content = re.sub(r'<style[^>]*>.*?</style>', '', content, flags=re.S | re.I)
        content = html.unescape(content)
        content = re.sub(r'<[^>]+>', ' ', content)
        content = re.sub(r'\s+', ' ', content)
        chunks = [content[i:i+500] for i in range(0, min(len(content), 50000), 500)]
        return [self.normalize_message(content=c.strip(), sender="author") for c in chunks if len(c.strip()) > 50]


# ============================================================
# Twitter/X Parser
# ============================================================

class TwitterParser(BaseParser):
    name = "twitter"
    extensions = [".json", ".csv", ".txt"]

    def parse(self, source: str) -> List[Dict]:
        ext = Path(source).suffix.lower()
        if ext == ".json":
            return self._parse_json(source)
        elif ext == ".csv":
            return self._parse_csv(source)
        return self._parse_txt(source)

    def _parse_json(self, path: str) -> List[Dict]:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        messages = []
        tweets = data if isinstance(data, list) else data.get("tweets", data.get("data", []))
        for tweet in tweets:
            text = tweet.get("full_text") or tweet.get("text", "")
            if not text:
                continue
            ts = tweet.get("created_at_unixtime", 0)
            if isinstance(ts, str):
                try:
                    ts = int(datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp())
                except:
                    ts = 0
            messages.append(self.normalize_message(content=text, sender=tweet.get("user", {}).get("screen_name", "unknown"), timestamp=ts))
        return messages

    def _parse_csv(self, path: str) -> List[Dict]:
        messages = []
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
        for line in lines[1:1000]:
            parts = line.split(",", 3)
            if len(parts) >= 2:
                text = parts[1].strip().strip('"')
                username = parts[3].strip().strip('"') if len(parts) > 3 else "unknown"
                if text:
                    messages.append(self.normalize_message(content=text, sender=username))
        return messages

    def _parse_txt(self, path: str) -> List[Dict]:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        messages = []
        for line in content.split('\n')[:1000]:
            line = line.strip()
            if len(line) > 10:
                messages.append(self.normalize_message(content=line, sender="user"))
        return messages


# ============================================================
# RSS Parser
# ============================================================

class RSSParser(BaseParser):
    name = "rss"
    extensions = [".xml", ".json", ".rss"]

    def parse(self, source: str) -> List[Dict]:
        ext = Path(source).suffix.lower()
        if ext == ".json":
            return self._parse_json_feed(source)
        return self._parse_xml_feed(source)

    def _parse_xml_feed(self, path: str) -> List[Dict]:
        import xml.etree.ElementTree as ET
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        messages = []
        try:
            root = ET.fromstring(content)
            for item in root.findall('.//item')[:200]:
                text = item.find('description') or item.find('content:encoded') or item.find('title')
                if text is not None and text.text:
                    text_content = html.unescape(text.text).strip()
                    if len(text_content) > 30:
                        messages.append(self.normalize_message(content=text_content[:500], sender=item.find('author').text if item.find('author') is not None else "feed"))
            if not messages:
                for entry in root.findall('.//entry')[:200]:
                    text = entry.find('content') or entry.find('summary') or entry.find('title')
                    if text is not None and text.text:
                        messages.append(self.normalize_message(content=html.unescape(text.text)[:500], sender="feed"))
        except ET.ParseError:
            pass
        return messages

    def _parse_json_feed(self, path: str) -> List[Dict]:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        messages = []
        items = data if isinstance(data, list) else data.get("items", data.get("entries", []))
        for item in items[:200]:
            text = item.get("content") or item.get("description") or item.get("title") or ""
            if isinstance(text, dict):
                text = text.get("content", "")
            if len(str(text)) > 30:
                messages.append(self.normalize_message(content=str(text)[:500], sender=item.get("author", item.get("creator", "feed")), timestamp=int(item.get("timestamp", 0) or 0)))
        return messages


# ============================================================
# Slack Parser
# ============================================================

class SlackParser(BaseParser):
    name = "slack"
    extensions = [".json"]

    def parse(self, source: str) -> List[Dict]:
        return self._parse_json(source)

    def _parse_json(self, path: str) -> List[Dict]:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        messages = []
        channels = data if isinstance(data, list) else data.get("channels", [])
        if not isinstance(channels, list):
            channels = [channels]
        for ch in channels:
            for msg in ch.get("messages", []):
                text = msg.get("text", "")
                if not text:
                    continue
                ts = int(msg.get("ts", 0))
                if isinstance(ts, float):
                    ts = int(ts)
                subtype = msg.get("subtype", "")
                if subtype in ["bot_message", "channel_join", "channel_leave"]:
                    continue
                messages.append(self.normalize_message(content=text, sender=msg.get("user", "unknown"), timestamp=ts))
        return messages


# ============================================================
# QQ Parser
# ============================================================

class QQParser(BaseParser):
    name = "qq"
    extensions = [".db", ".txt", ".json"]

    def parse(self, source: str) -> List[Dict]:
        ext = Path(source).suffix.lower()
        if ext == ".db":
            return self._parse_sqlite(source)
        elif ext == ".json":
            return self._parse_json(source)
        return self._parse_txt(source)

    def _parse_sqlite(self, path: str) -> List[Dict]:
        return WeChatParser()._parse_sqlite(path)

    def _parse_json(self, path: str) -> List[Dict]:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        messages = []
        for msg in (data if isinstance(data, list) else data.get("messages", [])):
            if msg.get("content"):
                messages.append(self.normalize_message(content=msg["content"], sender=msg.get("sender", msg.get("username", "unknown")), timestamp=int(msg.get("timestamp", 0) or 0), is_send=msg.get("is_send", False)))
        return messages

    def _parse_txt(self, path: str) -> List[Dict]:
        return WeChatParser()._parse_txt(path)


# ============================================================
# Signal Parser
# ============================================================

class SignalParser(BaseParser):
    name = "signal"
    extensions = [".json", ".txt"]

    def parse(self, source: str) -> List[Dict]:
        if source.endswith(".json"):
            return self._parse_json(source)
        return self._parse_txt(source)

    def _parse_json(self, path: str) -> List[Dict]:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        messages = []
        for conv in (data if isinstance(data, list) else data.get("conversations", [])):
            for msg in conv.get("messages", []):
                text = msg.get("text", msg.get("body", ""))
                if text:
                    messages.append(self.normalize_message(content=text, sender=msg.get("source", msg.get("sender", "unknown")), timestamp=int(msg.get("timestamp", 0) or 0), is_send=msg.get("type") == "outgoing"))
        return messages

    def _parse_txt(self, path: str) -> List[Dict]:
        return WeChatParser()._parse_txt(path)


# ============================================================
# Notes/Journal Parser
# ============================================================

class NotesParser(BaseParser):
    name = "notes"
    extensions = [".md", ".markdown", ".json", ".txt"]

    def parse(self, source: str) -> List[Dict]:
        if source.endswith(".json"):
            return self._parse_json(source)
        return self._parse_markdown(source)

    def _parse_json(self, path: str) -> List[Dict]:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        messages = []
        for note in (data if isinstance(data, list) else data.get("notes", data.get("entries", []))):
            text = note.get("content", note.get("text", note.get("body", "")))
            if text:
                messages.append(self.normalize_message(content=text, sender="author", timestamp=int(note.get("created_at", note.get("timestamp", 0)) or 0)))
        return messages

    def _parse_markdown(self, path: str) -> List[Dict]:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        blocks = re.split(r'\n\n+', content)
        messages = []
        date_pattern = re.compile(r'^#+\s+|^\d{4}-\d{2}-\d{2}')
        for block in blocks:
            block = block.strip()
            if len(block) < 20 or date_pattern.match(block):
                continue
            block = re.sub(r'^#+\s+', '', block)
            block = re.sub(r'\*{1,2}([^*]+)\*{1,2}', r'\1', block)
            block = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', block)
            if len(block) > 20:
                messages.append(self.normalize_message(content=block, sender="author"))
        return messages


# ============================================================
# Forum Parser
# ============================================================

class ForumParser(BaseParser):
    name = "forum"
    extensions = [".html", ".txt", ".json"]

    def parse(self, source: str) -> List[Dict]:
        ext = Path(source).suffix.lower()
        if ext == ".json":
            return self._parse_json(source)
        elif ext == ".html":
            return self._parse_html(source)
        return self._parse_txt(source)

    def _parse_html(self, path: str) -> List[Dict]:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        content = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.S | re.I)
        content = re.sub(r'<style[^>]*>.*?</style>', '', content, flags=re.S | re.I)
        content = html.unescape(content)
        messages = []
        post_pattern = re.compile(r'<div class="(?:post|message|body|content)"[^>]*>(.*?)</div>', re.S)
        posts = post_pattern.findall(content)
        for post in posts[:500]:
            post = re.sub(r'<[^>]+>', ' ', post)
            post = html.unescape(post)
            post = re.sub(r'\s+', ' ', post).strip()
            if len(post) > 20:
                messages.append(self.normalize_message(content=post[:1000], sender="user"))
        return messages

    def _parse_json(self, path: str) -> List[Dict]:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        messages = []
        for post in (data if isinstance(data, list) else data.get("posts", data.get("threads", []))):
            text = post.get("content", post.get("body", post.get("text", "")))
            if text:
                messages.append(self.normalize_message(content=text[:1000], sender=post.get("author", post.get("username", "user")), timestamp=int(post.get("created_at", 0) or 0)))
        return messages

    def _parse_txt(self, path: str) -> List[Dict]:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        messages = []
        for line in content.split('\n')[:1000]:
            line = line.strip()
            if ':' in line:
                idx = line.index(':')
                sender = line[:idx].strip()
                text = line[idx+1:].strip()
                if len(text) > 10:
                    messages.append(self.normalize_message(content=text, sender=sender))
        return messages


# ============================================================
# Custom/Generic Parser
# ============================================================

class CustomParser(BaseParser):
    name = "custom"
    extensions = [".txt", ".json", ".log", ".csv"]

    def parse(self, source: str) -> List[Dict]:
        if source.endswith(".json"):
            return self._parse_json(source)
        return self._parse_generic(source)

    def _parse_generic(self, path: str) -> List[Dict]:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
        messages = []
        for line in lines[:10000]:
            line = line.strip()
            if len(line) > 5:
                messages.append(self.normalize_message(content=line, sender="speaker"))
        return messages

    def _parse_json(self, path: str) -> List[Dict]:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        messages = []
        items = data if isinstance(data, list) else data.get("messages", data.get("data", [data]))
        for item in items:
            if isinstance(item, str):
                messages.append(self.normalize_message(content=item, sender="speaker"))
            elif item.get("content") or item.get("text"):
                messages.append(self.normalize_message(content=item.get("content", item.get("text", "")), sender=item.get("sender", item.get("author", "speaker")), timestamp=int(item.get("timestamp", 0) or 0), is_send=item.get("is_send", False)))
        return messages


# ============================================================
# Parser Registry
# ============================================================

class ParserRegistry:
    _parsers: List[BaseParser] = []

    @classmethod
    def register(cls, parser: BaseParser):
        cls._parsers.append(parser)

    @classmethod
    def get_parser(cls, source: str) -> BaseParser:
        ext = Path(source).suffix.lower()
        for parser in cls._parsers:
            if ext in parser.extensions:
                return parser
        return CustomParser()

    @classmethod
    def supported_formats(cls) -> List[Dict]:
        return [{"name": p.name, "extensions": p.extensions} for p in cls._parsers]


# Register all parsers
ParserRegistry.register(WeChatParser())
ParserRegistry.register(TelegramParser())
ParserRegistry.register(DiscordParser())
ParserRegistry.register(WhatsAppParser())
ParserRegistry.register(QQParser())
ParserRegistry.register(SignalParser())
ParserRegistry.register(EmailParser())
ParserRegistry.register(BookParser())
ParserRegistry.register(TwitterParser())
ParserRegistry.register(RSSParser())
ParserRegistry.register(SlackParser())
ParserRegistry.register(NotesParser())
ParserRegistry.register(ForumParser())
ParserRegistry.register(CustomParser())


# ============================================================
# Convenience Functions
# ============================================================

def auto_parse(source: str) -> List[Dict]:
    parser = ParserRegistry.get_parser(source)
    return parser.parse(source)


def list_supported_formats() -> List[Dict]:
    return ParserRegistry.supported_formats()


if __name__ == "__main__":
    print("=== Universal Distiller - Parser Registry ===")
    formats = list_supported_formats()
    print("Supported parsers:", len(formats))
    for f in formats:
        print("  -", f["name"], ":", f["extensions"])
    print()
    print("Ready: auto_parse('path/to/file')")