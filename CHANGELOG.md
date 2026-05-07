# Changelog

All notable changes to DistillAI are documented here.

## [v2.5.1] - 2026-05-08

### Fixed
- `keyword_embedding`: Fixed zero-vector bug for Chinese characters with single-byte hashes. Now uses multi-hash (8 positions per word) for proper semantic similarity across Chinese and English text.
- Vector search: Fixed `get_relevant()` parameter signature (`last_n` vs `k`). Search now returns meaningful scores (e.g., "股票投资" → "用户买了茅台股票" = 0.56).

### Added
- `distill/memory_vector.py`: FAISS-style vector memory with semantic search, time decay, importance weighting, and JSONL persistence.
- `distill/api/server.py` (v2.5 upgrade): Security middleware (API key auth, rate limiting, content filter, jailbreak detection), Swagger/OpenAPI auto-docs, role-based auth (read/write/admin), full CCv3 export endpoint, `/api/key` management.
- `README.md`: Restored full multilingual structure (CN/EN/JP) with i18n architecture, 14 input sources, all features documented.
- Multi-language SDK documentation in README.
- 14 input source types documented.

### Security
- All API endpoints protected by `@secure_require_key` and `@secure_require_role`.
- Default API key generation via `GET /api/key/generate-default`.
- Rate limiting (key/IP level), input sanitization, content policy enforcement.
- `--no-auth` and `--no-rate-limit` launch flags.

### Performance
- Provider auto-detection on startup (MiniMax → OpenAI → Anthropic → Ollama fallback chain).
- Vector memory with `get_relevant()` for O(1) context injection.

---

## [v2.5] - 2026-05-07

### Added
- `distill/security.py`: API key manager, rate limiter, input sanitizer, content filter.
- `distill/memory_v2.py`: Mem0-style semantic memory with time decay and tag search.
- `distill/memory_sqlite.py`: SQLite backend for persistent memory.
- Voice persona distiller: `voice_distiller.py` (WeChat audio → STT → prosody analysis → voice print → TTS output).
- Universal input parser: `universal_distiller.py` (14 source types).
- `distill/persona_skills.py`: 44 persona-specific skills.
- 26 built-in personas.
- Full documentation: LICENSE, README, CONTRIBUTING, SECURITY, ROADMAP.
- MIT License.

### Changed
- `wechat_distiller.py`: WeChat chat → persona distillation pipeline with card generation.

---

## [v2.4] - 2026-05-06

### Added
- 14 input sources: WeChat, QQ, Telegram, Discord, WhatsApp, Slack, Signal, Email, Books, Twitter, RSS, Forums, Notes, Custom text.

---

## [v2.3] - 2026-05-05

### Added
- Security layer: API authentication, rate limiting, jailbreak content filter.
- WeChat persona distiller with `WeChatParser` and `PersonaCardGenerator`.
- OpenClaw skill packager.

### Security
- Content filter with jailbreak detection.
- Anti-LLM bias correction via edge_cases + catchphrases.

---

## [v2.2] - 2026-05-04

### Added
- 26 persona-specific skill system: stock analysis, quant trading, value investing, etc.
- Skill routing engine.
- Buffett, Charlie Munger, Soros, Ray Dalio, Peter Lynch personas.
- Specialist thinking templates (巴菲特/禅师/沙雕网友/树洞姐姐/幽灵黑客).

---

## [v2.1] - 2026-05-03

### Added
- 5 language SDKs: Python, JavaScript, Go, Rust, Java, C#.
- Dockerfile for containerized deployment.
- SQLite memory backend.
- Bilingual CLI (Chinese/English).

---

## [v2.0] - 2026-05-02

### Added
- Mem0-style `SemanticMemory` with Add/Learn/Retrieve pipeline.
- `MemoryManager` with time decay and tag search.
- `DistillMarket` for persona sharing and marketplace.
- CCv3 (Character Card V3) export compatibility.
- Anti-LLM bias correction (edge_cases + catchphrases + thinking_prompt).

---

## [v1.2] - 2026-05-01

### Added
- 9 extended tools: code_run, unit_convert, translate, health_check, timer, habit, wisdom, schedule, emoji.

---

## [v1.1] - 2026-04-30

### Added
- Flask API server (ports 5000/5001).
- Multi-language README (CN/EN/JP).
- Feishu/Telegram/Discord webhooks.
- Emotion detection (positive/negative/neutral).

---

## [v1.0] - 2026-04-29

### Added
- Agent system with memory inheritance.
- Spawn system: clone/share/merge personas.
- 26 built-in personas.
- JoinQuant stock analysis integration.
- Complete tool system.

---

## [v0.3] - 2026-04-28

### Added
- CCv3 export for SillyTavern compatibility.
- Anti-LLM bias correction.
- edge_cases, catchphrases, thinking_prompt system.

---

## [v0.2] - 2026-04-27

### Added
- Bilingual CLI (ask/debate/compare/scenario commands).
- English personas.
- Game/animation archetypes.

---

## [v0.1.0] - 2026-04-26

### Added
- Initial release.
- 22 personas.
- JoinQuant stock analysis.
- Stock report generation.