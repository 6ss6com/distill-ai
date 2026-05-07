package distillai

/**
 * DistillAI Client SDK - Go
 *
 * go get github.com/6ss6com/distill-ai/clients/go
 *
 * Usage:
 *   client := distillai.NewClient("http://localhost:5000")
 *   reply, _ := client.Chat("巴菲特", "最近AI很火该投资吗")
 */

import (
    "bytes"
    "encoding/json"
    "fmt"
    "io"
    "net/http"
    "time"
)

// Client is the main DistillAI client
type Client struct {
    BaseURL string
    HTTP    *http.Client
}

// NewClient creates a new DistillAI client
func NewClient(baseURL string) *Client {
    return &Client{
        BaseURL: baseURL,
        HTTP: &http.Client{
            Timeout: 60 * time.Second,
            Transport: &http.Transport{
                MaxIdleConns:       100,
                IdleConnTimeout:     90 * time.Second,
                TLSHandshakeTimeout: 10 * time.Second,
            },
        },
    }
}

// Health returns server health status
func (c *Client) Health() (map[string]interface{}, error) {
    resp, err := c.HTTP.Get(c.BaseURL + "/health")
    if err != nil {
        return nil, err
    }
    defer resp.Body.Close()
    return readJSON(resp)
}

// Chat sends a simple chat request
func (c *Client) Chat(persona, message, userID string) (string, error) {
    body, _ := json.Marshal(map[string]interface{}{
        "persona": persona, "message": message, "user_id": userID,
    })
    resp, err := c.HTTP.Post(c.BaseURL+"/api/chat", "application/json", bytes.NewReader(body))
    if err != nil {
        return "", err
    }
    defer resp.Body.Close()
    data, err := readJSON(resp)
    if err != nil {
        return "", err
    }
    if reply, ok := data["reply"].(string); ok {
        return reply, nil
    }
    return "", fmt.Errorf("no reply field")
}

// AgentChat sends an agent chat request (with tools + emotion)
func (c *Client) AgentChat(persona, message, userID string) (map[string]interface{}, error) {
    body, _ := json.Marshal(map[string]interface{}{
        "persona": persona, "message": message, "user_id": userID,
    })
    resp, err := c.HTTP.Post(c.BaseURL+"/api/agent/chat", "application/json", bytes.NewReader(body))
    if err != nil {
        return nil, err
    }
    defer resp.Body.Close()
    return readJSON(resp)
}

// ClonePersona clones a persona to a new name
func (c *Client) ClonePersona(source, newName string) (map[string]interface{}, error) {
    body, _ := json.Marshal(map[string]interface{}{"source": source, "new_name": newName})
    resp, err := c.HTTP.Post(c.BaseURL+"/api/clone", "application/json", bytes.NewReader(body))
    if err != nil {
        return nil, err
    }
    defer resp.Body.Close()
    return readJSON(resp)
}

// MergePersonas merges two personas into a new one
func (c *Client) MergePersonas(name1, name2, newName string) (map[string]interface{}, error) {
    body, _ := json.Marshal(map[string]interface{}{"name1": name1, "name2": name2, "new_name": newName})
    resp, err := c.HTTP.Post(c.BaseURL+"/api/merge", "application/json", bytes.NewReader(body))
    if err != nil {
        return nil, err
    }
    defer resp.Body.Close()
    return readJSON(resp)
}

// SharePersona generates a share link for a persona
func (c *Client) SharePersona(persona string) (string, error) {
    resp, err := c.HTTP.Get(c.BaseURL + "/api/share/" + persona)
    if err != nil {
        return "", err
    }
    defer resp.Body.Close()
    data, err := readJSON(resp)
    if err != nil {
        return "", err
    }
    if link, ok := data["share_link"].(string); ok {
        return link, nil
    }
    return "", fmt.Errorf("no share_link field")
}

// ListPersonas returns all available personas
func (c *Client) ListPersonas() ([]string, error) {
    resp, err := c.HTTP.Get(c.BaseURL + "/api/personas")
    if err != nil {
        return nil, err
    }
    defer resp.Body.Close()
    data, err := readJSON(resp)
    if err != nil {
        return nil, err
    }
    if personas, ok := data["personas"].([]interface{}); ok {
        result := make([]string, len(personas))
        for i, p := range personas {
            if s, ok := p.(string); ok {
                result[i] = s
            }
        }
        return result, nil
    }
    return nil, fmt.Errorf("no personas field")
}

// GetMemory gets memory for a persona
func (c *Client) GetMemory(persona string) (map[string]interface{}, error) {
    resp, err := c.HTTP.Get(c.BaseURL + "/api/memory/" + persona)
    if err != nil {
        return nil, err
    }
    defer resp.Body.Close()
    return readJSON(resp)
}

// AddMemory adds a memory entry for a persona
func (c *Client) AddMemory(persona, content, eventType string, importance int) (map[string]interface{}, error) {
    body, _ := json.Marshal(map[string]interface{}{
        "content": content, "event_type": eventType, "importance": importance,
    })
    resp, err := c.HTTP.Post(c.BaseURL+"/api/memory/"+persona, "application/json", bytes.NewReader(body))
    if err != nil {
        return nil, err
    }
    defer resp.Body.Close()
    return readJSON(resp)
}

// Compare compares multiple personas on a question
func (c *Client) Compare(personas []string, question string) (map[string]string, error) {
    body, _ := json.Marshal(map[string]interface{}{"personas": personas, "question": question})
    resp, err := c.HTTP.Post(c.BaseURL+"/api/compare", "application/json", bytes.NewReader(body))
    if err != nil {
        return nil, err
    }
    defer resp.Body.Close()
    data, err := readJSON(resp)
    if err != nil {
        return nil, err
    }
    if results, ok := data["results"].(map[string]interface{}); ok {
        strMap := make(map[string]string)
        for k, v := range results {
            if s, ok := v.(string); ok {
                strMap[k] = s
            }
        }
        return strMap, nil
    }
    return nil, fmt.Errorf("no results field")
}

// Debate runs a debate between two personas
func (c *Client) Debate(persona1, persona2, topic string) (map[string]interface{}, error) {
    body, _ := json.Marshal(map[string]interface{}{
        "persona1": persona1, "persona2": persona2, "topic": topic,
    })
    resp, err := c.HTTP.Post(c.BaseURL+"/api/debate", "application/json", bytes.NewReader(body))
    if err != nil {
        return nil, err
    }
    defer resp.Body.Close()
    return readJSON(resp)
}

// Helper
func readJSON(resp *http.Response) (map[string]interface{}, error) {
    data, err := io.ReadAll(resp.Body)
    if err != nil {
        return nil, err
    }
    var result map[string]interface{}
    json.Unmarshal(data, &result)
    return result, nil
}