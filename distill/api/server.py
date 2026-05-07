"""
DistillAI Flask API Server v2.5 - Secured + Documented

Ports:
- 5000: REST API (chat/persona management)
- 5001: Webhook callbacks (Feishu/Discord/Telegram)
- 5002: Admin panel

Security:
- API Key authentication (Bearer token)
- Role-based access (read/write/admin)
- Rate limiting
- Input sanitization
- Jailbreak detection

Launch:
    python distill/api/server.py

API Docs: GET /docs
Health: GET /health
"""

import os, sys, json, re, threading
from pathlib import Path
from datetime import datetime
from functools import wraps

# Ensure distill module is importable
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path.home() / ".openclaw" / "workspace"))

from flask import Flask, request, jsonify
from distill import Distiller
from distill.agent import Agent
from distill.spawn import share_link, from_share_link


# ============================================================
# Security Import
# ============================================================

try:
    from distill.security import (
        APIKeyManager, RateLimiter, InputSanitizer, ContentFilter,
        require_api_key, require_role, sanitize_input, check_content,
        get_security, ensure_default_key
    )
    SECURITY_AVAILABLE = True
except ImportError:
    SECURITY_AVAILABLE = False
    print("[WARN] Security module not available")


# ============================================================
# Swagger / OpenAPI
# ============================================================

try:
    from flask_swagger_ui import get_swaggerui_blueprint
    SWAGGER_AVAILABLE = True
except ImportError:
    SWAGGER_AVAILABLE = False


# ============================================================
# App Factory
# ============================================================

def create_app(port: int = 5000, debug: bool = False,
               require_auth: bool = True, rate_limit: bool = True):
    app = Flask(__name__)
    app.config['DEBUG'] = debug

    # Init security
    sec = None
    if SECURITY_AVAILABLE and require_auth:
        sec = get_security()
        ensure_default_key()

    # Init distiller
    distiller = Distiller()

    # ========================================================
    # Middleware: Sanitization + Content Filter
    # ========================================================

    @app.before_request
    def security_middleware():
        if not SECURITY_AVAILABLE or not require_auth:
            return

        # Skip health/docs endpoints
        if request.path in ['/health', '/docs', '/swagger']:
            return

        # Check content (POST bodies)
        if request.method in ['POST', 'PUT', 'PATCH']:
            try:
                data = request.get_json(silent=True) or {}
                # Sanitize text fields
                for key in ['message', 'prompt', 'content', 'text']:
                    if key in data and isinstance(data[key], str):
                        clean, threats = sanitize_input(data[key], strict=False)
                        data[key] = clean

                        risk, issues = check_content(data[key])
                        if risk in ['danger', 'block']:
                            return jsonify({
                                "error": "Content policy violation",
                                "risk": risk,
                                "details": issues[:3]
                            }), 400
                # Store cleaned data
                request._secured_data = data
            except:
                pass

    # ========================================================
    # Decorators
    # ========================================================

    def secure_require_key(f):
        """Require valid API key"""
        @wraps(f)
        def decorated(*args, **kwargs):
            if not SECURITY_AVAILABLE or not require_auth:
                return f(*args, **kwargs)

            auth = request.headers.get("Authorization", "")
            if not auth.startswith("Bearer "):
                return jsonify({"error": "Authorization header required", "code": "AUTH_REQUIRED"}), 401

            key = auth[7:]
            sec = get_security()
            key_data = sec["key_manager"].verify_key(key)
            if not key_data:
                return jsonify({"error": "Invalid API key", "code": "AUTH_FAILED"}), 401

            # Rate limit
            if rate_limit:
                allowed, info = sec["rate_limiter"].check(key, "key")
                if not allowed:
                    resp = jsonify({"error": "Rate limit exceeded", "code": "RATE_LIMITED", **info})
                    resp.headers["Retry-After"] = str(info.get("retry_after", 60))
                    return resp, 429

            request.api_key_data = key_data
            return f(*args, **kwargs)
        return decorated

    def secure_require_role(role: str):
        """Require specific role"""
        def decorator(f):
            @wraps(f)
            def decorated(*args, **kwargs):
                if not SECURITY_AVAILABLE or not require_auth:
                    return f(*args, **kwargs)
                key_data = getattr(request, "api_key_data", None)
                if not key_data:
                    return jsonify({"error": "Not authenticated"}), 401
                hierarchy = {"read": 1, "write": 2, "admin": 3}
                user_level = hierarchy.get(key_data.get("role", ""), 0)
                required = hierarchy.get(role, 0)
                if user_level < required:
                    return jsonify({"error": f"Requires {role} role"}), 403
                return f(*args, **kwargs)
            return decorated
        return decorator

    # ========================================================
    # OpenAPI / Swagger Schema
    # ========================================================

    OPENAPI_SCHEMA = {
        "openapi": "3.0.3",
        "info": {
            "title": "DistillAI API",
            "description": "AI Persona Platform - DistillAI: 蒸馏人格AI平台，支持26种预训练人格、聊天、分身管理、记忆存储。",
            "version": "2.5.0",
            "contact": {"name": "DistillAI", "url": "https://github.com/6ss6com/distill-ai"}
        },
        "servers": [{"url": f"http://localhost:{port}"}],
        "paths": {
            "/health": {
                "get": {
                    "summary": "Health check",
                    "responses": {"200": {"description": "OK"}}
                }
            },
            "/api/chat": {
                "post": {
                    "summary": "Simple chat",
                    "security": [{"BearerAuth": []}],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["persona", "message"],
                                    "properties": {
                                        "persona": {"type": "string", "example": "巴菲特"},
                                        "message": {"type": "string", "example": "茅台值得买吗？"},
                                        "user_id": {"type": "string", "example": "user123"}
                                    }
                                }
                            }
                        }
                    },
                    "responses": {"200": {"description": "Chat response"}}
                }
            },
            "/api/agent/chat": {
                "post": {
                    "summary": "Full agent chat (with tools + emotion)",
                    "security": [{"BearerAuth": []}],
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["persona", "message"],
                                    "properties": {
                                        "persona": {"type": "string"},
                                        "message": {"type": "string"},
                                        "user_id": {"type": "string"}
                                    }
                                }
                            }
                        }
                    },
                    "responses": {"200": {"description": "Full agent response"}}
                }
            },
            "/api/personas": {
                "get": {
                    "summary": "List all personas",
                    "security": [{"BearerAuth": []}],
                    "responses": {"200": {"description": "Persona list"}}
                }
            },
            "/api/clone": {
                "post": {
                    "summary": "Clone a persona",
                    "security": [{"BearerAuth": []}],
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["source", "new_name"],
                                    "properties": {
                                        "source": {"type": "string"},
                                        "new_name": {"type": "string"}
                                    }
                                }
                            }
                        }
                    },
                    "responses": {"200": {"description": "Cloned"}}
                }
            },
            "/api/memory/{persona}": {
                "get": {
                    "summary": "Get persona memory",
                    "security": [{"BearerAuth": []}],
                    "parameters": [{"name": "persona", "in": "path", "required": True, "schema": {"type": "string"}}],
                    "responses": {"200": {"description": "Memory data"}}
                },
                "post": {
                    "summary": "Add memory",
                    "security": [{"BearerAuth": []}],
                    "parameters": [{"name": "persona", "in": "path", "required": True, "schema": {"type": "string"}}],
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "content": {"type": "string"},
                                        "event_type": {"type": "string"},
                                        "importance": {"type": "integer"}
                                    }
                                }
                            }
                        }
                    },
                    "responses": {"200": {"description": "Added"}}
                }
            },
            "/api/ccv3/{persona}": {
                "get": {
                    "summary": "Export CCv3 character card",
                    "security": [{"BearerAuth": []}],
                    "parameters": [{"name": "persona", "in": "path", "required": True, "schema": {"type": "string"}}],
                    "responses": {"200": {"description": "CCv3 JSON"}}
                }
            },
            "/api/debate": {
                "post": {
                    "summary": "Two-persona debate",
                    "security": [{"BearerAuth": []}],
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["persona1", "persona2", "topic"],
                                    "properties": {
                                        "persona1": {"type": "string"},
                                        "persona2": {"type": "string"},
                                        "topic": {"type": "string"}
                                    }
                                }
                            }
                        }
                    },
                    "responses": {"200": {"description": "Debate result"}}
                }
            },
            "/api/key": {
                "get": {
                    "summary": "List API keys",
                    "security": [{"BearerAuth": []}],
                    "responses": {"200": {"description": "Key list"}}
                }
            }
        },
        "components": {
            "securitySchemes": {
                "BearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "description": "API Key (Bearer token)"
                }
            }
        }
    }

    # ========================================================
    # Routes
    # ========================================================

    @app.route("/health")
    def health():
        keys_info = {}
        if SECURITY_AVAILABLE:
            keys_info = get_security()["key_manager"].get_stats()
        return jsonify({
            "status": "ok",
            "version": "2.5.0",
            "security_enabled": SECURITY_AVAILABLE and require_auth,
            "port": port,
            "time": datetime.now().isoformat(),
            "keys": keys_info,
        })

    # Swagger UI
    if SWAGGER_AVAILABLE:
        SWAGGER_URL = '/docs'
        API_URL = f"/openapi.json"
        app.register_blueprint(
            get_swaggerui_blueprint(SWAGGER_URL, API_URL),
            url_prefix=SWAGGER_URL
        )

        @app.route("/openapi.json")
        def swagger_json():
            return jsonify(OPENAPI_SCHEMA)

    @app.route("/docs")
    def docs():
        return jsonify({
            "title": "DistillAI API Documentation",
            "version": "2.5.0",
            "swagger_ui": "/docs",
            "openapi_schema": "/openapi.json",
            "security": "Bearer token (Authorization header)",
            "endpoints": list(OPENAPI_SCHEMA["paths"].keys()),
            "example_key": "distill_xxxxxxxxxxxxxxxxxxxx (generate via /api/key)"
        })

    # ---- Chat ----

    @app.route("/api/chat", methods=["POST"])
    @secure_require_key
    @secure_require_role("read")
    def chat():
        data = getattr(request, "_secured_data", None) or request.get_json() or {}
        persona = data.get("persona", "沙雕网友")
        message = data.get("message", "")
        user_id = data.get("user_id", "api_user")
        try:
            reply = distiller.chat(persona, message, user_id=user_id)
            return jsonify({"reply": reply, "persona": persona})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/agent/chat", methods=["POST"])
    @secure_require_key
    @secure_require_role("read")
    def agent_chat():
        data = getattr(request, "_secured_data", None) or request.get_json() or {}
        persona = data.get("persona", "沙雕网友")
        message = data.get("message", "")
        user_id = data.get("user_id", "api_user")
        try:
            result = distiller.agent_chat(persona, message, user_id=user_id)
            return jsonify(result)
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    # ---- Personas ----

    @app.route("/api/personas")
    @secure_require_key
    @secure_require_role("read")
    def list_personas():
        personas = distiller.list_personas()
        return jsonify({"count": len(personas), "personas": personas})

    @app.route("/api/personas/<name>")
    @secure_require_key
    @secure_require_role("read")
    def get_persona(name: str):
        card = distiller.get_persona_card(name)
        if card:
            return jsonify(card)
        return jsonify({"error": "Persona not found"}), 404

    # ---- Clone/Merge/Share ----

    @app.route("/api/clone", methods=["POST"])
    @secure_require_key
    @secure_require_role("write")
    def clone():
        data = request.get_json() or {}
        source = data.get("source")
        new_name = data.get("new_name")
        if not source or not new_name:
            return jsonify({"error": "source and new_name required"}), 400
        try:
            distiller.clone_persona(source, new_name)
            return jsonify({"ok": True, "persona": new_name})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/merge", methods=["POST"])
    @secure_require_key
    @secure_require_role("write")
    def merge():
        data = request.get_json() or {}
        name1 = data.get("name1")
        name2 = data.get("name2")
        new_name = data.get("new_name")
        if not all([name1, name2, new_name]):
            return jsonify({"error": "name1, name2, new_name required"}), 400
        try:
            distiller.merge_personas(name1, name2, new_name)
            return jsonify({"ok": True, "persona": new_name})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/share/<name>")
    @secure_require_key
    @secure_require_role("read")
    def share(name: str):
        try:
            link = share_link(name)
            return jsonify({"share_link": link})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/import", methods=["POST"])
    @secure_require_key
    @secure_require_role("write")
    def import_persona():
        data = request.get_json() or {}
        link = data.get("link")
        new_name = data.get("new_name")
        if not link:
            return jsonify({"error": "link required"}), 400
        try:
            from_share_link(link, new_name)
            return jsonify({"ok": True, "persona": new_name})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    # ---- Memory ----

    @app.route("/api/memory/<name>", methods=["GET"])
    @secure_require_key
    @secure_require_role("read")
    def get_memory(name: str):
        try:
            mem = distiller.get_memory(name)
            return jsonify(mem)
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/memory/<name>", methods=["POST"])
    @secure_require_key
    @secure_require_role("write")
    def add_memory(name: str):
        data = request.get_json() or {}
        content = data.get("content", "")
        event_type = data.get("event_type", "custom")
        importance = data.get("importance", 2)
        try:
            distiller.add_memory(name, content, event_type=event_type, importance=importance)
            return jsonify({"ok": True})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    # ---- Market ----

    @app.route("/api/market/list")
    @secure_require_key
    @secure_require_role("read")
    def market_list():
        try:
            from distill.spawn import DistillMarket
            market = DistillMarket()
            listings = market.list_public()
            return jsonify({"count": len(listings), "listings": listings})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/market/publish", methods=["POST"])
    @secure_require_key
    @secure_require_role("write")
    def market_publish():
        data = request.get_json() or {}
        persona = data.get("persona")
        if not persona:
            return jsonify({"error": "persona required"}), 400
        try:
            from distill.spawn import DistillMarket
            market = DistillMarket()
            url = market.publish(persona)
            return jsonify({"ok": True, "url": url})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    # ---- Compare/Debate ----

    @app.route("/api/compare", methods=["POST"])
    @secure_require_key
    @secure_require_role("read")
    def compare():
        data = request.get_json() or {}
        personas = data.get("personas", [])
        question = data.get("question", "")
        if len(personas) < 2:
            return jsonify({"error": "At least 2 personas required"}), 400
        try:
            results = {}
            for p in personas:
                reply = distiller.chat(p, question)
                results[p] = reply
            return jsonify({"question": question, "results": results})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/debate", methods=["POST"])
    @secure_require_key
    @secure_require_role("read")
    def debate():
        data = request.get_json() or {}
        p1 = data.get("persona1")
        p2 = data.get("persona2")
        topic = data.get("topic")
        if not all([p1, p2, topic]):
            return jsonify({"error": "persona1, persona2, topic required"}), 400
        try:
            intro1 = distiller.chat(p1, f"开场陈述: {topic}")
            intro2 = distiller.chat(p2, f"开场陈述: {topic}")
            rebuttal1 = distiller.chat(p1, f"反驳对方: {intro2[:200]}")
            rebuttal2 = distiller.chat(p2, f"反驳对方: {intro1[:200]}")
            return jsonify({
                "topic": topic,
                p1: {"opening": intro1, "rebuttal": rebuttal1},
                p2: {"opening": intro2, "rebuttal": rebuttal2}
            })
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    # ---- CCv3 Export ----

    @app.route("/api/ccv3/<name>")
    @secure_require_key
    @secure_require_role("read")
    def ccv3_export(name: str):
        try:
            card = distiller.get_persona_card(name)
            if not card:
                return jsonify({"error": "Persona not found"}), 404

            # Build full CCv3 format
            thinking = card.get("thinking_prompt", "")
            samples = card.get("speech_samples", [])

            ccv3 = {
                "spec": "CCv3.0",
                "name": name,
                "description": card.get("core_identity", {}).get("description", ""),
                "avatar": card.get("avatar", ""),
                "personality": card.get("values", [])[:5],
                "first_msg": samples[0] if samples else f"你好，我是{name}。有什么可以帮你的吗？",
                "messages": {
                    "examples": [[s, f"[{name}的回应: ...]"] for s in samples[:5]]
                },
                "creators": {"name": "DistillAI", "url": "https://github.com/6ss6com/distill-ai"},
                "character_version": "1.0",
                "alternating_io": True,
                "tags": card.get("knowledge", []) + card.get("values", []),
                "meta": {
                    "source": "distillai",
                    "version": "2.5.0",
                    "exported_at": datetime.now().isoformat()
                },
                "# NOTE": "Full CCv3 format. Import into SillyTavern or any CCv3-compatible client."
            }
            return jsonify(ccv3)
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    # ---- API Key Management ----

    @app.route("/api/key", methods=["GET"])
    @secure_require_key
    @secure_require_role("admin")
    def list_keys():
        if not SECURITY_AVAILABLE:
            return jsonify({"error": "Security not available"}), 500
        keys = get_security()["key_manager"].list_keys()
        stats = get_security()["key_manager"].get_stats()
        return jsonify({"keys": keys, "stats": stats})

    @app.route("/api/key", methods=["POST"])
    @secure_require_key
    @secure_require_role("admin")
    def create_key():
        if not SECURITY_AVAILABLE:
            return jsonify({"error": "Security not available"}), 500
        data = request.get_json() or {}
        name = data.get("name", "new_key")
        role = data.get("role", "read")
        expires = data.get("expires_days", 365)
        key_id, full_key = get_security()["key_manager"].generate_key(name, role, expires)
        return jsonify({"key_id": key_id, "api_key": full_key, "role": role})

    @app.route("/api/key/<key_id>", methods=["DELETE"])
    @secure_require_key
    @secure_require_role("admin")
    def revoke_key(key_id: str):
        if not SECURITY_AVAILABLE:
            return jsonify({"error": "Security not available"}), 500
        ok = get_security()["key_manager"].revoke_key(key_id)
        return jsonify({"ok": ok})

    @app.route("/api/key/generate-default")
    def generate_default_key():
        """Generate default admin key (no auth required for first-time setup)"""
        if not SECURITY_AVAILABLE:
            return jsonify({"error": "Security not available"}), 500
        key_id, full_key = ensure_default_key()
        if not full_key:
            return jsonify({"error": "Default key already exists or setup failed"}), 400
        return jsonify({"key_id": key_id, "api_key": full_key, "warning": "Store this key securely. It will not be shown again."})

    return app


# ============================================================
# Webhook Server (port 5001)
# ============================================================

def create_webhook_app(port: int = 5001):
    app = Flask(__name__)
    distiller = Distiller()

    @app.route("/webhook/feishu", methods=["POST"])
    def feishu():
        try:
            data = request.get_json() or {}
            content = data.get("content", "")
            sender = data.get("sender", {})
            open_id = sender.get("sender_id", {}).get("open_id", "unknown")
            # Simple reply
            reply = distiller.chat("沙雕网友", content[:200], user_id=open_id)
            return jsonify({"reply": reply})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/webhook/telegram", methods=["POST"])
    def telegram():
        try:
            data = request.get_json() or {}
            msg = data.get("message", {})
            text = msg.get("text", "")
            chat_id = msg.get("chat", {}).get("id", "unknown")
            reply = distiller.chat("沙雕网友", text[:200], user_id=str(chat_id))
            return jsonify({"reply": reply})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/webhook/discord", methods=["POST"])
    def discord():
        try:
            data = request.get_json() or {}
            content = data.get("content", "")
            user_id = data.get("author", {}).get("id", "unknown")
            reply = distiller.chat("沙雕网友", content[:200], user_id=str(user_id))
            return jsonify({"reply": reply})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/webhook/generic", methods=["POST"])
    def generic():
        try:
            data = request.get_json() or {}
            message = data.get("message", "")
            user_id = data.get("user_id", "generic")
            persona = data.get("persona", "沙雕网友")
            reply = distiller.chat(persona, message[:200], user_id=user_id)
            return jsonify({"reply": reply})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    return app


# ============================================================
# Multi-Port Launch
# ============================================================

def main():
    import argparse
    parser = argparse.ArgumentParser(description="DistillAI API Server v2.5")
    parser.add_argument("--port", type=int, default=5000, help="REST API port (default 5000)")
    parser.add_argument("--webhook-port", type=int, default=5001, help="Webhook port (default 5001)")
    parser.add_argument("--no-auth", action="store_true", help="Disable API key authentication")
    parser.add_argument("--no-rate-limit", action="store_true", help="Disable rate limiting")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind")
    args = parser.parse_args()

    print(f"DistillAI API Server v2.5")
    print(f"REST API: http://{args.host}:{args.port}")
    print(f"Webhooks: http://{args.host}:{args.webhook_port}")
    print(f"Swagger UI: http://{args.host}:{args.port}/docs")
    print(f"Auth: {'Disabled' if args.no_auth else 'Enabled (Bearer token)'}")
    print(f"Rate limit: {'Disabled' if args.no_rate_limit else 'Enabled'}")

    # Start webhook server in background
    if args.webhook_port != args.port:
        from werkzeug.serving import make_server
        webhook_app = create_webhook_app(args.webhook_port)
        server = make_server(args.host, args.webhook_port, webhook_app, threaded=True)
        t = threading.Thread(target=server.serve_forever, daemon=True)
        t.start()
        print(f"[OK] Webhook server started on :{args.webhook_port}")

    # Start REST API
    app = create_app(
        port=args.port,
        require_auth=not args.no_auth,
        rate_limit=not args.no_rate_limit
    )
    print(f"[OK] REST API server starting on :{args.port}")
    app.run(host=args.host, port=args.port, debug=False, threaded=True)


if __name__ == "__main__":
    main()