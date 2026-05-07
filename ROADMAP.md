# DistillAI Roadmap

> Last updated: 2026-05-08 | Current: **v2.5.1**

---

## v2.5.1 (Current) - 2026-05-08 ✅

### What's Done
- [x] Vector memory (FAISS-style semantic search)
- [x] Security middleware (API key + rate limiting + content filter)
- [x] Swagger/OpenAPI auto docs
- [x] Role-based auth (read/write/admin)
- [x] CCv3 full export
- [x] Multilingual README (CN/EN/JP)
- [x] Multi-hash keyword embedding (Chinese + English)

---

## v3.0 - Next Release

### Planned
- [ ] **向量知识库增强** - FAISS/AnnLite real integration, GPU acceleration
- [ ] **更多人格蒸馏** - 按需蒸馏垂类人格（律师/医生/教师/销售）
- [ ] **CCv3 SillyTavern完整兼容** - full alternate_greetings, character_book, extensions
- [ ] **SillyTavern集成** - one-click export → SillyTavern角色卡
- [ ] **Docker Hub发布** - auto-build + docker pull distill-ai
- [ ] **pip install** - `pip install distill-ai`
- [ ] **webhook增强** - Slack, Teams, WhatsApp native webhooks
- [ ] **流式输出** - streaming responses for real-time chat
- [ ] **多轮对话上下文** - conversation history management
- [ ] **分享链接** - public persona sharing marketplace
- [ ] **CLI增强** - interactive TUI, auto-completion

---

## v3.1 - Platform Ecosystem

### Planned
- [ ] **OpenClaw Skill发布** - distill persona → OpenClaw skill (one command)
- [ ] **微信Bot集成** - WeChat Work (企业微信) native bot
- [ ] **飞书Bot** - Feishu (Lark) native bot with message threading
- [ ] **Discord/Telegram Bot** - full bot with slash commands
- [ ] **API Key市场** - developer API key marketplace
- [ ] **定价策略** - free tier / pro tier / enterprise

---

## v3.2 - Enterprise & Advanced

### Planned
- [ ] **分布式部署** - Redis pub/sub, multiple workers
- [ ] **向量数据库集成** - Pinecone / Weaviate / Qdrant cloud support
- [ ] **角色市场** - public persona marketplace (distill.cloud)
- [ ] **Custom模型微调** - fine-tune a persona from chat logs (LoRA)
- [ ] **多语言人格** - 中文/English/日本語/한국어 personas
- [ ] **语音视频人格** - voice clone + video avatar
- [ ] **实时视频对话** - AI avatar video calls

---

## v3.3 - Security & Compliance

### Planned
- [ ] **SOC2/GDPR合规** - enterprise compliance
- [ ] **加密存储** - at-rest encryption for personas
- [ ] **审计日志** - full API audit trail
- [ ] **IP白名单** - IP-based access control
- [ ] **商业License** - proprietary licensing option

---

## Ideas Backlog

- [ ] 心理医生人格 (therapy persona)
- [ ] 销售冠军人格 (sales persona)
- [ ] 律师人格 (legal advisor persona)
- [ ] 教师人格 (tutor persona)
- [ ] 代码审查人格 (code reviewer persona)
- [ ] 投资组合优化 (portfolio optimizer)
- [ ] 多Agent辩论系统 (multi-agent debate)
- [ ] 角色扮演游戏DM人格 (D&D dungeon master)
- [ ] AI角色扮演故事生成器
- [ ] 会议纪要AI人格

---

## Version History

| Version | Date | Key Changes |
|---------|------|-------------|
| v2.5.1 | 2026-05-08 | Vector memory fix, security middleware, multilingual README |
| v2.5 | 2026-05-07 | Voice distiller, security layer, 26 personas |
| v2.4 | 2026-05-06 | 14 input source types |
| v2.3 | 2026-05-05 | Security layer, anti-LLM bias |
| v2.2 | 2026-05-04 | 26 persona skill system |
| v2.1 | 2026-05-03 | 5 language SDKs, SQLite memory |
| v2.0 | 2026-05-02 | Mem0 memory, CCv3 export |
| v1.0 | 2026-04-29 | Agent system, spawn/clone/merge |