import requests

OLLAMA_API = "http://localhost:11434"

def chat_with_ollama(model: str, messages: list):
    payload = {
        "model": model,
        "messages": messages,
        "stream": False  # Disable streaming for simplicity
    }
    r = requests.post(f"{OLLAMA_API}/api/chat", json=payload)
    r.raise_for_status()
    return r.json()["message"]["content"]

if __name__ == "__main__":
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Write a short poem about the moon."}
    ]
    result = chat_with_ollama("llama3", messages)
    print("Chat API Response:")
    print(result)
