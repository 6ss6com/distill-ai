# DistillAI

## Project Overview

**DistillAI** is a persona distillation system — extract AI personality agents from chat logs, voice messages, emails, books, and various digital sources.

## Quick Start

```bash
# Chat persona distillation
from wechat_distiller import WeChatParser, PersonaDistiller, PersonaCardGenerator
parser = WeChatParser()
parser.load_txt("chat.txt")
analysis = PersonaDistiller().analyze(parser.messages, target_sender="张三")
persona = PersonaCardGenerator().generate(analysis, name="张三")
```

```bash
# Voice persona distillation
from voice_distiller import VoiceDistiller
vd = VoiceDistiller()
report = vd.distill("voice_message.mp3")
audio = vd.speak("Hello from your voice persona", voice_config=report)
```

```bash
# Flask API server
python distill/api/server.py
# REST API: http://localhost:5000
# Webhooks: http://localhost:5001
```

## Features

- **26 built-in personas** with unique skills
- **14 input sources**: WeChat, QQ, Telegram, Discord, WhatsApp, Slack, Signal, Email, Books, Twitter, RSS, Forums, Notes, Custom text
- **Voice persona distillation**: audio → STT → prosody analysis → voice print → TTS output
- **OpenClaw integration**: package personas as OpenClaw skills
- **Multi-language SDKs**: Python, JavaScript, Go, Rust, Java, C#

## Architecture

```
distill/
├── agent.py           # Core agent runtime
├── providers/         # Model providers (MiniMax/OpenAI/Ollama)
├── tools/             # 18 built-in tools
├── persona_skills.py   # 44 persona-specific skills
├── memory_v2.py       # Mem0-style semantic memory
├── memory_sqlite.py    # SQLite backend
├── security.py         # API auth, rate limiting, content filter
├── personas/          # 26 built-in personas
├── api/server.py       # Flask REST API
wechat_distiller.py     # Chat persona distiller
universal_distiller.py  # Universal input parser
voice_distiller.py      # Voice persona distiller
```

## License

This project is licensed under **MIT License**. See [LICENSE](LICENSE) for details.

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Security

See [SECURITY.md](SECURITY.md) for vulnerability reporting.