/**
 * DistillAI Client SDK - JavaScript / Node.js
 *
 * npm install axios
 *
 * Usage:
 *   const { DistillAIClient } = require('./distill_client.js');
 *   const client = new DistillAIClient('http://localhost:5000');
 *   const reply = await client.chat('巴菲特', '最近AI很火该投资吗');
 */

const axios = require('axios');

class DistillAIClient {
  /**
   * DistillAI Multi-Language Client - JavaScript版本
   * 支持: Node.js / 浏览器 / Bun / Deno
   */
  constructor(baseUrl = 'http://localhost:5000', timeout = 60000) {
    this.baseUrl = baseUrl.replace(/\/$/, '');
    this.timeout = timeout;
    this.client = axios.create({
      timeout,
      headers: { 'User-Agent': 'DistillAI-JS-SDK/2.0' }
    });
  }

  // ===== 基础 =====
  async health() {
    const r = await this.client.get(`${this.baseUrl}/health`);
    return r.data;
  }

  // ===== 聊天 =====
  async chat(persona, message, userId = 'default') {
    const r = await this.client.post(`${this.baseUrl}/api/chat`, {
      persona, message, user_id: userId
    });
    return r.data.reply || '';
  }

  async agentChat(persona, message, userId = 'default') {
    const r = await this.client.post(`${this.baseUrl}/api/agent/chat`, {
      persona, message, user_id: userId
    });
    return r.data; // {reply, emotion, tools_used, thinking}
  }

  // ===== 分身管理 =====
  async spawnInfo(persona) {
    const r = await this.client.get(`${this.baseUrl}/api/spawn/${encodeURIComponent(persona)}`);
    return r.data;
  }

  async resetSpawn(persona, userId = 'default') {
    const r = await this.client.post(`${this.baseUrl}/api/spawn/${encodeURIComponent(persona)}/reset`, {
      user_id: userId
    });
    return r.data;
  }

  async clonePersona(source, newName) {
    const r = await this.client.post(`${this.baseUrl}/api/clone`, { source, new_name: newName });
    return r.data;
  }

  async mergePersonas(name1, name2, newName) {
    const r = await this.client.post(`${this.baseUrl}/api/merge`, {
      name1, name2, new_name: newName
    });
    return r.data;
  }

  async sharePersona(persona) {
    const r = await this.client.get(`${this.baseUrl}/api/share/${encodeURIComponent(persona)}`);
    return r.data.share_link || '';
  }

  async importPersona(link, newName = null) {
    const payload = { link };
    if (newName) payload.new_name = newName;
    const r = await this.client.post(`${this.baseUrl}/api/import`, payload);
    return r.data;
  }

  // ===== 记忆 =====
  async getMemory(persona) {
    const r = await this.client.get(`${this.baseUrl}/api/memory/${encodeURIComponent(persona)}`);
    return r.data;
  }

  async addMemory(persona, content, eventType = 'custom', importance = 2) {
    const r = await this.client.post(`${this.baseUrl}/api/memory/${encodeURIComponent(persona)}`, {
      content, event_type: eventType, importance
    });
    return r.data;
  }

  // ===== 市场 =====
  async marketList() {
    const r = await this.client.get(`${this.baseUrl}/api/market/list`);
    return r.data.listings || [];
  }

  async marketPublish(persona, description = '', tags = []) {
    const r = await this.client.post(`${this.baseUrl}/api/market/publish`, {
      persona, description, tags
    });
    return r.data;
  }

  // ===== 对比/辩论 =====
  async compare(personas, question) {
    const r = await this.client.post(`${this.baseUrl}/api/compare`, { personas, question });
    return r.data.results || {};
  }

  async debate(persona1, persona2, topic) {
    const r = await this.client.post(`${this.baseUrl}/api/debate`, { persona1, persona2, topic });
    return r.data;
  }

  // ===== CCv3 =====
  async exportCCV3(persona) {
    const r = await this.client.get(`${this.baseUrl}/api/ccv3/${encodeURIComponent(persona)}`);
    return r.data;
  }

  // ===== 列表 =====
  async listPersonas() {
    const r = await this.client.get(`${this.baseUrl}/api/personas`);
    return r.data.personas || [];
  }
}

// ===== Webhook Client =====
class DistillAIWebhook {
  constructor(webhookUrl = 'http://localhost:5001') {
    this.baseUrl = webhookUrl.replace(/\/$/, '');
    this.client = axios.create({ timeout: 30000 });
  }

  async feishu(text, persona = '沙雕网友', userId = 'feishu_user') {
    const r = await this.client.post(`${this.baseUrl}/webhook/feishu`, {
      content: text,
      persona,
      sender: { sender_id: { open_id: userId } }
    });
    return r.data;
  }

  async feishuReceive(message, persona = '沙雕网友') {
    const r = await this.client.post(`${this.baseUrl}/webhook/feishu/receive`, {
      message, persona
    });
    return r.data;
  }

  async telegram(text, chatId = null, persona = '沙雕网友') {
    const r = await this.client.post(`${this.baseUrl}/webhook/telegram`, {
      message: { text, chat: { id: chatId }, from: { id: 'user' } },
      persona
    });
    return r.data;
  }

  async discord(content, userId = null, persona = '沙雕网友') {
    const r = await this.client.post(`${this.baseUrl}/webhook/discord`, {
      content, author: { id: userId }, persona
    });
    return r.data;
  }

  async generic(message, persona = '沙雕网友', userId = 'generic') {
    const r = await this.client.post(`${this.baseUrl}/webhook/generic`, {
      message, persona, user_id: userId
    });
    return r.data;
  }
}

module.exports = { DistillAIClient, DistillAIWebhook };

// ESM export
if (typeof module.exports === 'object' && module.exports && module.exports.__esModule) {
  // already esm
}