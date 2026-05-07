/**
 * DistillAI Client SDK - Rust
 *
 * Add to Cargo.toml:
 * distillai = { git = "https://github.com/6ss6com/distill-ai", package = "distillai-client" }
 *
 * Or copy this file as src/distillai.rs and add to lib.rs
 *
 * Usage:
 *   let client = DistillAIClient::new("http://localhost:5000");
 *   let reply = client.chat("巴菲特", "最近AI很火该投资吗").await?;
 */

use reqwest::Client;
use serde::{Deserialize, Serialize};
use std::time::Duration;

#[derive(Debug, Serialize)]
struct ChatRequest {
    persona: String,
    message: String,
    user_id: String,
}

#[derive(Debug, Deserialize)]
struct ChatResponse {
    reply: Option<String>,
    #[serde(flatten)]
    extra: serde_json::Value,
}

#[derive(Debug, Deserialize)]
struct HealthResponse {
    status: String,
    port: u16,
    time: String,
}

#[derive(Debug, Deserialize)]
struct PersonasResponse {
    count: usize,
    personas: Vec<String>,
}

#[derive(Debug, Deserialize)]
struct AgentChatResponse {
    reply: Option<String>,
    emotion: Option<String>,
    tools_used: Option<Vec<String>>,
    thinking: Option<String>,
    persona: Option<String>,
}

pub struct DistillAIClient {
    base_url: String,
    http: Client,
}

impl DistillAIClient {
    /// Create a new DistillAI client
    pub fn new(base_url: &str) -> Self {
        let http = Client::builder()
            .timeout(Duration::from_secs(60))
            .user_agent("DistillAI-Rust-SDK/2.0")
            .build()
            .unwrap_or_else(|_| Client::new());

        Self {
            base_url: base_url.trim_end_matches('/').to_string(),
            http,
        }
    }

    /// Health check
    pub async fn health(&self) -> Result<HealthResponse, Box<dyn std::error::Error>> {
        let url = format!("{}/health", self.base_url);
        let resp = self.http.get(&url).send().await?;
        let data: HealthResponse = resp.json().await?;
        Ok(data)
    }

    /// Simple chat
    pub async fn chat(&self, persona: &str, message: &str) -> Result<String, Box<dyn std::error::Error>> {
        let url = format!("{}/api/chat", self.base_url);
        let body = ChatRequest {
            persona: persona.to_string(),
            message: message.to_string(),
            user_id: "default".to_string(),
        };
        let resp = self.http.post(&url).json(&body).send().await?;
        let data: ChatResponse = resp.json().await?;
        Ok(data.reply.unwrap_or_default())
    }

    /// Agent chat (with tools + emotion)
    pub async fn agent_chat(&self, persona: &str, message: &str, user_id: &str) -> Result<AgentChatResponse, Box<dyn std::error::Error>> {
        let url = format!("{}/api/agent/chat", self.base_url);
        let body = ChatRequest {
            persona: persona.to_string(),
            message: message.to_string(),
            user_id: user_id.to_string(),
        };
        let resp = self.http.post(&url).json(&body).send().await?;
        let data: AgentChatResponse = resp.json().await?;
        Ok(data)
    }

    /// Clone persona
    pub async fn clone_persona(&self, source: &str, new_name: &str) -> Result<serde_json::Value, Box<dyn std::error::Error>> {
        let url = format!("{}/api/clone", self.base_url);
        let body = serde_json::json!({
            "source": source,
            "new_name": new_name
        });
        let resp = self.http.post(&url).json(&body).send().await?;
        let data: serde_json::Value = resp.json().await?;
        Ok(data)
    }

    /// Merge personas
    pub async fn merge_personas(&self, name1: &str, name2: &str, new_name: &str) -> Result<serde_json::Value, Box<dyn std::error::Error>> {
        let url = format!("{}/api/merge", self.base_url);
        let body = serde_json::json!({
            "name1": name1,
            "name2": name2,
            "new_name": new_name
        });
        let resp = self.http.post(&url).json(&body).send().await?;
        let data: serde_json::Value = resp.json().await?;
        Ok(data)
    }

    /// Share persona
    pub async fn share_persona(&self, persona: &str) -> Result<String, Box<dyn std::error::Error>> {
        let url = format!("{}/api/share/{}", self.base_url, persona);
        let resp = self.http.get(&url).send().await?;
        let data: serde_json::Value = resp.json().await?;
        Ok(data["share_link"].as_str().unwrap_or("").to_string())
    }

    /// List all personas
    pub async fn list_personas(&self) -> Result<Vec<String>, Box<dyn std::error::Error>> {
        let url = format!("{}/api/personas", self.base_url);
        let resp = self.http.get(&url).send().await?;
        let data: PersonasResponse = resp.json().await?;
        Ok(data.personas)
    }

    /// Get memory for a persona
    pub async fn get_memory(&self, persona: &str) -> Result<serde_json::Value, Box<dyn std::error::Error>> {
        let url = format!("{}/api/memory/{}", self.base_url, persona);
        let resp = self.http.get(&url).send().await?;
        let data: serde_json::Value = resp.json().await?;
        Ok(data)
    }

    /// Add memory
    pub async fn add_memory(&self, persona: &str, content: &str, event_type: &str, importance: u8) -> Result<serde_json::Value, Box<dyn std::error::Error>> {
        let url = format!("{}/api/memory/{}", self.base_url, persona);
        let body = serde_json::json!({
            "content": content,
            "event_type": event_type,
            "importance": importance
        });
        let resp = self.http.post(&url).json(&body).send().await?;
        let data: serde_json::Value = resp.json().await?;
        Ok(data)
    }

    /// Compare multiple personas
    pub async fn compare(&self, personas: Vec<&str>, question: &str) -> Result<serde_json::Value, Box<dyn std::error::Error>> {
        let url = format!("{}/api/compare", self.base_url);
        let body = serde_json::json!({
            "personas": personas,
            "question": question
        });
        let resp = self.http.post(&url).json(&body).send().await?;
        let data: serde_json::Value = resp.json().await?;
        Ok(data)
    }

    /// Debate between two personas
    pub async fn debate(&self, persona1: &str, persona2: &str, topic: &str) -> Result<serde_json::Value, Box<dyn std::error::Error>> {
        let url = format!("{}/api/debate", self.base_url);
        let body = serde_json::json!({
            "persona1": persona1,
            "persona2": persona2,
            "topic": topic
        });
        let resp = self.http.post(&url).json(&body).send().await?;
        let data: serde_json::Value = resp.json().await?;
        Ok(data)
    }

    /// Export CCv3 character card
    pub async fn export_ccv3(&self, persona: &str) -> Result<serde_json::Value, Box<dyn std::error::Error>> {
        let url = format!("{}/api/ccv3/{}", self.base_url, persona);
        let resp = self.http.get(&url).send().await?;
        let data: serde_json::Value = resp.json().await?;
        Ok(data)
    }
}