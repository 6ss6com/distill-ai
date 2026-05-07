"""
DistillAI Flask API Server - 多端口商用手部署

端口规划:
- 5000: REST API (聊天/分身管理)
- 5001: Webhook回调 (飞书/Discord/Telegram)
- 5002: Admin管理面板

启动方式:
    python distill/api/server.py

API文档: GET /docs
健康检查: GET /health
"""
import os, sys, json, threading
from pathlib import Path
from datetime import datetime

# 确保distill模块可导入
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path.home() / ".openclaw" / "workspace"))

from flask import Flask, request, jsonify
from distill import Distiller
from distill.agent import Agent
from distill.spawn import share_link, from_share_link

# ===== 多端口启动 =====
def create_app(port: int, debug: bool = False):
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'distill-ai-secret-' + str(port))
    app.port = port

    d = None  # lazy init

    def get_distiller():
        nonlocal d
        if d is None:
            d = Distiller()
        return d

    # ===== 基础路由 =====
    @app.route('/health', methods=['GET'])
    def health():
        return jsonify({
            'status': 'ok',
            'port': port,
            'time': datetime.now().isoformat(),
            'distiller': 'ready' if d else 'initializing'
        })

    # ===== 聊天 API =====
    @app.route('/api/chat', methods=['POST'])
    def chat():
        """POST /api/chat {"persona": "巴菲特", "message": "最近市场怎么样"}"""
        data = request.get_json() or {}
        persona = data.get('persona')
        message = data.get('message', '')
        user_id = data.get('user_id', 'api')

        if not persona or not message:
            return jsonify({'error': 'persona and message required'}), 400

        try:
            dist = get_distiller()
            if persona == '_agent':
                # 使用Agent.run() (带工具+情感)
                agent = dist.create_spawn(data.get('agent_name', '巴菲特'))
                result = agent.run(message, user_id=user_id, verbose=False)
                return jsonify({
                    'reply': result['reply'],
                    'emotion': result['emotion'],
                    'tools_used': result['tools_used'],
                    'persona': agent.persona_name
                })
            else:
                reply = dist.chat(persona, message)
                return jsonify({'reply': reply, 'persona': persona})

        except Exception as e:
            return jsonify({'error': str(e)}), 500

    # ===== Agent模式 (带工具+记忆) =====
    @app.route('/api/agent/chat', methods=['POST'])
    def agent_chat():
        """POST /api/agent/chat {"persona": "巴菲特", "message": "腾讯多少", "user_id": "owner"}"""
        data = request.get_json() or {}
        persona = data.get('persona', '巴菲特')
        message = data.get('message', '')
        user_id = data.get('user_id', 'default')

        try:
            agent = get_distiller().create_spawn(persona)
            result = agent.run(message, user_id=user_id, verbose=False)
            return jsonify({
                'reply': result['reply'],
                'emotion': result['emotion'],
                'emotion_intensity': result.get('emotion_intensity', 0),
                'tools_used': result['tools_used'],
                'thinking': result.get('thinking', '')[:200],
                'persona': agent.persona_name
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    # ===== 分身管理 =====
    @app.route('/api/spawn/<persona_name>', methods=['GET'])
    def spawn_info(persona_name):
        """获取分身信息"""
        try:
            dist = get_distiller()
            agent = dist.create_spawn(persona_name)
            return jsonify({
                'persona': persona_name,
                'tools': [t.name for t in agent._tools],
                'avatar': agent.avatar,
                'core_identity': str(agent.core_identity)[:100]
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 404

    @app.route('/api/spawn/<persona_name>/reset', methods=['POST'])
    def reset_spawn(persona_name):
        """重置分身对话上下文"""
        data = request.get_json() or {}
        user_id = data.get('user_id', 'default')
        try:
            dist = get_distiller()
            agent = dist.create_spawn(persona_name)
            agent.reset(user_id=user_id)
            return jsonify({'status': 'reset', 'persona': persona_name, 'user_id': user_id})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    # ===== 分身克隆/合并 =====
    @app.route('/api/clone', methods=['POST'])
    def clone():
        """POST /api/clone {"source": "巴菲特", "new_name": "价值投资者"}"""
        data = request.get_json() or {}
        source = data.get('source')
        new_name = data.get('new_name')
        if not source or not new_name:
            return jsonify({'error': 'source and new_name required'}), 400
        try:
            dist = get_distiller()
            agent = dist.clone_persona(source, new_name)
            return jsonify({'status': 'cloned', 'new_persona': new_name, 'tools': [t.name for t in agent._tools]})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/merge', methods=['POST'])
    def merge():
        """POST /api/merge {"name1": "巴菲特", "name2": "禅师", "new_name": "投资禅师"}"""
        data = request.get_json() or {}
        name1 = data.get('name1')
        name2 = data.get('name2')
        new_name = data.get('new_name')
        if not all([name1, name2, new_name]):
            return jsonify({'error': 'name1, name2, new_name required'}), 400
        try:
            dist = get_distiller()
            agent = dist.merge_personas(name1, name2, new_name)
            return jsonify({'status': 'merged', 'new_persona': new_name})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    # ===== 分身分享 =====
    @app.route('/api/share/<persona_name>', methods=['GET'])
    def share(persona_name):
        """生成分身分享链接"""
        try:
            link = get_distiller().share_persona(persona_name)
            return jsonify({'share_link': link, 'persona': persona_name})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/import', methods=['POST'])
    def import_persona():
        """POST /api/import {"link": "distill://...", "new_name": "我的分身"}"""
        data = request.get_json() or {}
        link = data.get('link')
        new_name = data.get('new_name')
        if not link:
            return jsonify({'error': 'link required'}), 400
        try:
            agent = from_share_link(link)
            return jsonify({'status': 'imported', 'persona': agent.persona_name})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    # ===== 记忆管理 =====
    @app.route('/api/memory/<persona_name>', methods=['GET'])
    def get_memory(persona_name):
        """获取分身记忆"""
        try:
            dist = get_distiller()
            agent = dist.create_spawn(persona_name)
            mem = agent._memory
            return jsonify({
                'persona': persona_name,
                'events_count': len(mem.get_events()),
                'history_turns': len(mem._history),
                'recent_events': [e['content'] for e in mem.get_events()[:5]]
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/memory/<persona_name>', methods=['POST'])
    def add_memory():
        """POST /api/memory {"event_type": "custom", "content": "用户今天买了茅台"}"""
        data = request.get_json() or {}
        content = data.get('content')
        event_type = data.get('event_type', 'custom')
        importance = data.get('importance', 2)
        persona_name = request.view_args['persona_name']

        try:
            dist = get_distiller()
            agent = dist.create_spawn(persona_name)
            agent.remember(user_id='api', what=content, event_type=event_type)
            return jsonify({'status': 'added', 'persona': persona_name})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    # ===== 市场 =====
    @app.route('/api/market/list', methods=['GET'])
    def market_list():
        """列出本地市场的分身"""
        try:
            dist = get_distiller()
            market = dist.get_market()
            listings = market.browse()
            return jsonify({'count': len(listings), 'listings': [
                {'id': l['id'], 'name': l.get('card', {}).get('name', '?'),
                 'tags': l.get('tags', []), 'rating': l.get('rating', 0)}
                for l in listings
            ]})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/market/publish', methods=['POST'])
    def market_publish():
        """POST /api/market/publish {"persona": "巴菲特", "description": "...", "tags": ["投资"]}"""
        data = request.get_json() or {}
        persona = data.get('persona')
        desc = data.get('description', '')
        tags = data.get('tags', [])
        try:
            dist = get_distiller()
            agent = dist.create_spawn(persona)
            market = dist.get_market()
            listing_id = market.publish(agent, description=desc, tags=tags)
            return jsonify({'status': 'published', 'listing_id': listing_id})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    # ===== 对比/辩论 =====
    @app.route('/api/compare', methods=['POST'])
    def compare():
        """POST /api/compare {"personas": ["巴菲特", "禅师"], "question": "50万怎么投"}"""
        data = request.get_json() or {}
        personas = data.get('personas', [])
        question = data.get('question', '')
        if not personas or not question:
            return jsonify({'error': 'personas and question required'}), 400
        try:
            dist = get_distiller()
            results = dist.compare(personas, question)
            return jsonify({'results': {k: v[:300] for k, v in results.items()}})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/debate', methods=['POST'])
    def debate():
        """POST /api/debate {"persona1": "巴菲特", "persona2": "禅师", "topic": "要不要辞职创业"}"""
        data = request.get_json() or {}
        p1 = data.get('persona1')
        p2 = data.get('persona2')
        topic = data.get('topic')
        if not all([p1, p2, topic]):
            return jsonify({'error': 'persona1, persona2, topic required'}), 400
        try:
            dist = get_distiller()
            result = dist.debate(p1, p2, topic)
            return jsonify(result)
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    # ===== CCv3导出 =====
    @app.route('/api/ccv3/<persona_name>', methods=['GET'])
    def export_ccv3(persona_name):
        """导出CCv3格式角色卡"""
        try:
            dist = get_distiller()
            ccv3 = dist.export_ccv3(persona_name)
            return jsonify(ccv3)
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    # ===== Persona列表 =====
    @app.route('/api/personas', methods=['GET'])
    def list_personas():
        """列出所有可用人格"""
        try:
            dist = get_distiller()
            personas = dist.list_personas()
            return jsonify({'count': len(personas), 'personas': personas})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    return app


# ===== Webhook Server (端口5001) =====
def create_webhook_server():
    """飞书/Discord/Telegram Webhook处理服务器"""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('WEBHOOK_SECRET', 'distill-webhook-secret')

    d = None
    def get_distiller():
        nonlocal d
        if d is None:
            d = Distiller()
        return d

    # ===== 飞书 Webhook =====
    @app.route('/webhook/feishu', methods=['POST'])
    def feishu_webhook():
        """接收飞书 events API 回调"""
        data = request.get_json() or {}
        # 验证签名(如果配置了)
        # event = data.get('event', {})
        # schema验证
        try:
            # 提取用户消息
            msg_type = data.get('msg_type', 'text')
            content = data.get('content', '{}')
            if msg_type == 'text':
                import json as json_mod
                text = json_mod.loads(content).get('text', '')
            else:
                return jsonify({'error': 'unsupported msg_type'}), 400

            # 获取from_user_id
            sender = data.get('sender', {})
            user_id = sender.get('sender_id', {}).get('open_id', 'feishu_user')

            # 使用默认人格或指定
            dist = get_distiller()
            persona = data.get('persona', '沙雕网友')
            agent = dist.create_spawn(persona)
            result = agent.run(text, user_id=user_id, verbose=False)

            return jsonify({
                'status': 'ok',
                'reply': result['reply'],
                'emotion': result['emotion']
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    # ===== 飞书 Message API (被动回复) =====
    @app.route('/webhook/feishu/receive', methods=['POST'])
    def feishu_receive():
        """
        飞书 消息回调租户授权模式
        POST body: { message: {...}, ... }
        """
        data = request.get_json() or {}
        try:
            msg = data.get('message', {})
            content_str = msg.get('content', '{}')
            import json as json_mod
            content = json_mod.loads(content_str)
            text = content.get('text', '').strip()
            user_open_id = msg.get('open_id', 'unknown')

            if not text:
                return jsonify({'status': 'ignored'})

            # 构建回复
            dist = get_distiller()
            persona = data.get('persona', '沙雕网友')
            agent = dist.create_spawn(persona)
            result = agent.run(text, user_id=user_open_id, verbose=False)

            # 返回reply用于后续发消息API调用
            return jsonify({
                'status': 'ok',
                'reply': result['reply'],
                'emotion': result['emotion'],
                'tools': result['tools_used']
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    # ===== Discord Webhook =====
    @app.route('/webhook/discord', methods=['POST'])
    def discord_webhook():
        """Discord interaction webhook (slash commands / messages)"""
        data = request.get_json() or {}
        try:
            # Discord message
            if data.get('t') == 'MESSAGE_CREATE' or 'content' in data:
                content = data.get('content', '')
                author = data.get('author', {})
                user_id = author.get('id', 'discord')

                if not content or content.startswith('!'):
                    return jsonify({'status': 'ignored'})

                dist = get_distiller()
                persona = data.get('persona', '沙雕网友')
                agent = dist.create_spawn(persona)
                result = agent.run(content, user_id=user_id, verbose=False)

                return jsonify({
                    'reply': result['reply'],
                    'emotion': result['emotion']
                })
            return jsonify({'status': 'ok'})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    # ===== Telegram Bot Webhook =====
    @app.route('/webhook/telegram', methods=['POST'])
    def telegram_webhook():
        """Telegram bot webhook handler"""
        data = request.get_json() or {}
        try:
            update = data.get('message', {})
            text = update.get('text', '')
            chat_id = update.get('chat', {}).get('id', 'unknown')
            user_id = str(update.get('from', {}).get('id', 'telegram'))

            if not text:
                return jsonify({'status': 'ignored'})

            dist = get_distiller()
            persona = data.get('persona', '沙雕网友')
            agent = dist.create_spawn(persona)
            result = agent.run(text, user_id=user_id, verbose=False)

            return jsonify({
                'status': 'ok',
                'reply': result['reply'],
                'chat_id': chat_id
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    # ===== 通用Webhook (可用于自定义集成) =====
    @app.route('/webhook/generic', methods=['POST'])
    def generic_webhook():
        """通用Webhook: POST {"persona": "...", "message": "...", "user_id": "..."}"""
        data = request.get_json() or {}
        persona = data.get('persona', '沙雕网友')
        message = data.get('message', '')
        user_id = data.get('user_id', 'generic')

        if not message:
            return jsonify({'error': 'message required'}), 400

        try:
            dist = get_distiller()
            agent = dist.create_spawn(persona)
            result = agent.run(message, user_id=user_id, verbose=False)
            return jsonify({
                'reply': result['reply'],
                'emotion': result['emotion'],
                'tools_used': result['tools_used']
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/health', methods=['GET'])
    def health():
        return jsonify({'status': 'webhook_server_ok', 'time': datetime.now().isoformat()})

    return app


# ===== 启动器 =====
def run_multi_port():
    """启动多端口服务器"""
    from werkzeug.serving import run_simple

    print('=' * 60)
    print('DistillAI Multi-Port API Server')
    print('=' * 60)
    print('REST API:     http://localhost:5000')
    print('Webhooks:     http://localhost:5001')
    print('API Docs:     http://localhost:5000/docs')
    print()
    print('Endpoints:')
    print('  POST /api/chat          - 简单聊天')
    print('  POST /api/agent/chat   - Agent聊天(带工具)')
    print('  POST /api/clone         - 克隆分身')
    print('  POST /api/merge         - 合并分身')
    print('  GET  /api/share/<name>  - 生成分享链接')
    print('  POST /api/import        - 导入分享链接')
    print('  POST /webhook/generic   - 通用Webhook')
    print('  POST /webhook/feishu    - 飞书回调')
    print('  POST /webhook/telegram  - Telegram机器人')
    print('  POST /webhook/discord   - Discord机器人')
    print('=' * 60)

    # 使用threading分别启动
    import threading

    app1 = create_app(5000)
    app2 = create_webhook_server()

    t1 = threading.Thread(target=lambda: app1.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False))
    t2 = threading.Thread(target=lambda: app2.run(host='0.0.0.0', port=5001, debug=False, use_reloader=False))

    t1.start()
    t2.start()

    print('Servers started! Press Ctrl+C to stop.')

    try:
        t1.join()
        t2.join()
    except KeyboardInterrupt:
        print('\nShutting down...')


if __name__ == '__main__':
    run_multi_port()