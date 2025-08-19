import requests

OLLAMA_API = "http://localhost:11434"
CHAT_MODEL = "llama3"

def call_ollama_chat(messages):
    payload = {
        "model": CHAT_MODEL,
        "messages": messages,
        "stream": False  # Turn off streaming so .json() works
    }
    resp = requests.post(f"{OLLAMA_API}/api/chat", json=payload)
    resp.raise_for_status()
    data = resp.json()
    print("Response JSON:", data)
    # In /api/chat the content is under ["message"]["content"]
    return data["message"]["content"].strip()

# --- Query rewriting ---
def rewrite_query(query: str) -> str:
    messages = [
        {
            "role": "system",
            "content": "You are a query rewriting assistant. Make the query clearer and more specific."
        },
        {
            "role": "user",
            "content": query
        },
    ]
    rewritten = call_ollama_chat(messages)
    return rewritten.strip()

if __name__ == "__main__":
    original_query = "weather in toronto tomorrow"
    new_query = rewrite_query(original_query)
    print("Rewritten query:", new_query)
