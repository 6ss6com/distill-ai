using System;
using System.Net.Http;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;
using System.Collections.Generic;

namespace DistillAI
{
    /// <summary>
    /// DistillAI Client SDK - C# (.NET)
    ///
    /// Usage:
    ///   var client = new DistillAIClient("http://localhost:5000");
    ///   string reply = await client.ChatAsync("巴菲特", "最近AI很火该投资吗");
    /// </summary>
    public class DistillAIClient : IDisposable
    {
        private readonly HttpClient _http;
        private readonly string _baseUrl;

        public DistillAIClient(string baseUrl = "http://localhost:5000", int timeoutSeconds = 60)
        {
            _baseUrl = baseUrl.TrimEnd('/');
            _http = new HttpClient
            {
                Timeout = TimeSpan.FromSeconds(timeoutSeconds)
            };
            _http.DefaultRequestHeaders.Add("User-Agent", "DistillAI-CSharp-SDK/2.0");
        }

        // ===== Basic =====

        public async Task<JsonDocument> HealthAsync()
        {
            var resp = await _http.GetAsync($"{_baseUrl}/health");
            var json = await resp.Content.ReadAsStringAsync();
            return JsonDocument.Parse(json);
        }

        // ===== Chat =====

        public async Task<string> ChatAsync(string persona, string message, string userId = "default")
        {
            var body = new { persona, message, user_id = userId };
            var json = await PostAsync("/api/chat", body);
            return json.RootElement.GetProperty("reply").GetString() ?? "";
        }

        public async Task<JsonDocument> AgentChatAsync(string persona, string message, string userId = "default")
        {
            var body = new { persona, message, user_id = userId };
            return await PostAsync("/api/agent/chat", body);
        }

        // ===== Persona Management =====

        public async Task<JsonDocument> ClonePersonaAsync(string source, string newName)
        {
            var body = new { source, new_name = newName };
            return await PostAsync("/api/clone", body);
        }

        public async Task<JsonDocument> MergePersonasAsync(string name1, string name2, string newName)
        {
            var body = new { name1, name2, new_name = newName };
            return await PostAsync("/api/merge", body);
        }

        public async Task<string> SharePersonaAsync(string persona)
        {
            var json = await GetAsync($"/api/share/{Uri.EscapeDataString(persona)}");
            return json.RootElement.GetProperty("share_link").GetString() ?? "";
        }

        // ===== Memory =====

        public async Task<JsonDocument> GetMemoryAsync(string persona)
        {
            return await GetAsync($"/api/memory/{Uri.EscapeDataString(persona)}");
        }

        public async Task<JsonDocument> AddMemoryAsync(string persona, string content, string eventType = "custom", int importance = 2)
        {
            var body = new { content, event_type = eventType, importance };
            return await PostAsync($"/api/memory/{Uri.EscapeDataString(persona)}", body);
        }

        // ===== Market =====

        public async Task<List<JsonElement>> MarketListAsync()
        {
            var json = await GetAsync("/api/market/list");
            var listings = json.RootElement.GetProperty("listings");
            var result = new List<JsonElement>();
            foreach (var item in listings.EnumerateArray())
                result.Add(item);
            return result;
        }

        // ===== Compare/Debate =====

        public async Task<JsonDocument> CompareAsync(string[] personas, string question)
        {
            var body = new { personas, question };
            return await PostAsync("/api/compare", body);
        }

        public async Task<JsonDocument> DebateAsync(string persona1, string persona2, string topic)
        {
            var body = new { persona1, persona2, topic };
            return await PostAsync("/api/debate", body);
        }

        // ===== CCv3 =====

        public async Task<JsonDocument> ExportCCV3Async(string persona)
        {
            return await GetAsync($"/api/ccv3/{Uri.EscapeDataString(persona)}");
        }

        // ===== List =====

        public async Task<string[]> ListPersonasAsync()
        {
            var json = await GetAsync("/api/personas");
            var personas = json.RootElement.GetProperty("personas");
            var result = new List<string>();
            foreach (var p in personas.EnumerateArray())
                result.Add(p.GetString() ?? "");
            return result.ToArray();
        }

        // ===== HTTP Helpers =====

        private async Task<JsonDocument> GetAsync(string path)
        {
            var resp = await _http.GetAsync($"{_baseUrl}{path}");
            var json = await resp.Content.ReadAsStringAsync();
            return JsonDocument.Parse(json);
        }

        private async Task<JsonDocument> PostAsync<T>(string path, T body)
        {
            var json = JsonSerializer.Serialize(body);
            var content = new StringContent(json, Encoding.UTF8, "application/json");
            var resp = await _http.PostAsync($"{_baseUrl}{path}", content);
            var responseJson = await resp.Content.ReadAsStringAsync();
            return JsonDocument.Parse(responseJson);
        }

        public void Dispose()
        {
            _http?.Dispose();
        }
    }
}