import requests
from typing import List, Dict

OLLAMA_API = "http://ollama-service-internal:11434"
#CHROMA_DB = "127.0.0.1"
CHAT_MODEL = "llama3"

# Step 1: Call Ollama embedding API
# Step 2: Ask to genearate expanded queries 
# Step 3: Return list of expanded queries

def expand_query(original_query: str) -> List[str]:
    """
    Use an LLM to expand a query into related terms or phrases.
    Returns a list of expanded query strings.
    """
    messages = [
        {
            "role": "system",
            "content": (
                "You are an expert query expansion assistant. "
                "Take the user's query and generate 3-5 related queries "
                "or terms that capture the same topic or related concepts."
            )
        },
        {
            "role": "user",
            "content": f"Original query: '{original_query}'"
        }
    ]
    
    payload = {
        "model": CHAT_MODEL,
        "messages": messages,
        "stream": False
    }
    resp = requests.post(f"{OLLAMA_API}/api/chat", json=payload)
    resp.raise_for_status()
    data = resp.json()
    
    # The response is usually a single string, split by lines or commas
    expanded_text = data["message"]["content"]
    
    # Split into separate expanded queries
    expanded_queries = [q.strip() for q in expanded_text.replace("-", "\n").split("\n") if q.strip()]
    
    return expanded_queries

# --- Example Usage ---
if __name__ == "__main__":
    original = "The life in Canada"
    expanded_queries = expand_query(original)
    
    print("Original query:", original)
    print("Expanded queries:")
    for q in expanded_queries:
        print("-", q)
