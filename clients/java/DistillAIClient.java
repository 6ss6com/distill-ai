package com.distillai;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import java.util.List;
import java.util.Map;

/**
 * DistillAI Client SDK - Java
 *
 * Add to pom.xml:
 * <dependency>
 *   <groupId>com.distillai</groupId>
 *   <artifactId>distillai-client</artifactId>
 *   <version>2.0.0</version>
 * </dependency>
 *
 * Or copy this file and compile manually.
 *
 * Usage:
 *   DistillAIClient client = new DistillAIClient("http://localhost:5000");
 *   String reply = client.chat("巴菲特", "最近AI很火该投资吗");
 */
public class DistillAIClient {

    private final String baseUrl;
    private final HttpClient http;

    public DistillAIClient(String baseUrl) {
        this.baseUrl = baseUrl.replaceAll("/$", "");
        this.http = HttpClient.newBuilder()
                .connectTimeout(Duration.ofSeconds(10))
                .build();
    }

    // ===== HTTP helpers =====

    private String post(String path, String body) throws Exception {
        HttpRequest req = HttpRequest.newBuilder()
                .uri(URI.create(baseUrl + path))
                .header("Content-Type", "application/json")
                .header("User-Agent", "DistillAI-Java-SDK/2.0")
                .POST(HttpRequest.BodyPublishers.ofString(body))
                .build();
        HttpResponse<String> resp = http.send(req, HttpResponse.BodyHandlers.ofString());
        return resp.body();
    }

    private String get(String path) throws Exception {
        HttpRequest req = HttpRequest.newBuilder()
                .uri(URI.create(baseUrl + path))
                .header("User-Agent", "DistillAI-Java-SDK/2.0")
                .GET()
                .build();
        HttpResponse<String> resp = http.send(req, HttpResponse.BodyHandlers.ofString());
        return resp.body();
    }

    private String postRaw(String path, String body) throws Exception {
        return post(path, body);
    }

    // ===== Basic =====

    public Map<?, ?> health() throws Exception {
        String resp = get("/health");
        return parseJSON(resp);
    }

    // ===== Chat =====

    public String chat(String persona, String message) throws Exception {
        String body = String.format("{\"persona\":\"%s\",\"message\":\"%s\",\"user_id\":\"default\"}",
                escapeJSON(persona), escapeJSON(message));
        String resp = post("/api/chat", body);
        Map<?, ?> json = parseJSON(resp);
        Object reply = json.get("reply");
        return reply != null ? reply.toString() : "";
    }

    public Map<?, ?> agentChat(String persona, String message, String userId) throws Exception {
        String body = String.format("{\"persona\":\"%s\",\"message\":\"%s\",\"user_id\":\"%s\"}",
                escapeJSON(persona), escapeJSON(message), escapeJSON(userId));
        String resp = post("/api/agent/chat", body);
        return parseJSON(resp);
    }

    // ===== Persona Management =====

    public Map<?, ?> clonePersona(String source, String newName) throws Exception {
        String body = String.format("{\"source\":\"%s\",\"new_name\":\"%s\"}", escapeJSON(source), escapeJSON(newName));
        return parseJSON(post("/api/clone", body));
    }

    public Map<?, ?> mergePersonas(String name1, String name2, String newName) throws Exception {
        String body = String.format("{\"name1\":\"%s\",\"name2\":\"%s\",\"new_name\":\"%s\"}",
                escapeJSON(name1), escapeJSON(name2), escapeJSON(newName));
        return parseJSON(post("/api/merge", body));
    }

    public String sharePersona(String persona) throws Exception {
        String resp = get("/api/share/" + urlEncode(persona));
        Map<?, ?> json = parseJSON(resp);
        Object link = json.get("share_link");
        return link != null ? link.toString() : "";
    }

    // ===== Memory =====

    public Map<?, ?> getMemory(String persona) throws Exception {
        return parseJSON(get("/api/memory/" + urlEncode(persona)));
    }

    public Map<?, ?> addMemory(String persona, String content, String eventType, int importance) throws Exception {
        String body = String.format("{\"content\":\"%s\",\"event_type\":\"%s\",\"importance\":%d}",
                escapeJSON(content), escapeJSON(eventType), importance);
        return parseJSON(post("/api/memory/" + urlEncode(persona), body));
    }

    // ===== Market =====

    public List<?> marketList() throws Exception {
        String resp = get("/api/market/list");
        Map<?, ?> json = parseJSON(resp);
        Object listings = json.get("listings");
        if (listings instanceof List) {
            return (List<?>) listings;
        }
        return List.of();
    }

    // ===== Compare/Debate =====

    public Map<?, ?> compare(List<String> personas, String question) throws Exception {
        String personasStr = String.join("\",\"", personas);
        String body = String.format("{\"personas\":[\"%s\"],\"question\":\"%s\"}", personasStr, escapeJSON(question));
        String resp = post("/api/compare", body);
        return parseJSON(resp);
    }

    public Map<?, ?> debate(String persona1, String persona2, String topic) throws Exception {
        String body = String.format("{\"persona1\":\"%s\",\"persona2\":\"%s\",\"topic\":\"%s\"}",
                escapeJSON(persona1), escapeJSON(persona2), escapeJSON(topic));
        return parseJSON(post("/api/debate", body));
    }

    // ===== CCv3 =====

    public Map<?, ?> exportCCV3(String persona) throws Exception {
        return parseJSON(get("/api/ccv3/" + urlEncode(persona)));
    }

    // ===== List =====

    public List<String> listPersonas() throws Exception {
        String resp = get("/api/personas");
        Map<?, ?> json = parseJSON(resp);
        Object personas = json.get("personas");
        if (personas instanceof List) {
            @SuppressWarnings("unchecked")
            List<String> result = (List<String>) personas;
            return result;
        }
        return List.of();
    }

    // ===== JSON helpers =====

    private Map<?, ?> parseJSON(String json) throws Exception {
        // Simple manual parser (no external deps)
        return com.fasterxml.jackson.databind.ObjectMapper().readValue(json, Map.class);
    }

    private String escapeJSON(String s) {
        return s.replace("\\", "\\\\").replace("\"", "\\\"").replace("\n", "\\n").replace("\r", "\\r");
    }

    private String urlEncode(String s) {
        return java.net.URLEncoder.encode(s, java.nio.charset.StandardCharsets.UTF_8);
    }
}