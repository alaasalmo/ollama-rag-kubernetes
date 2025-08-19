import requests

OLLAMA_API = "http://localhost:11434"

def generate_with_ollama(model: str, prompt: str):
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False  # Disable streaming for simplicity
    }
    r = requests.post(f"{OLLAMA_API}/api/generate", json=payload)
    r.raise_for_status()
    return r.json()["response"]

if __name__ == "__main__":
    result = generate_with_ollama("llama3", "Write a short poem about the moon.")
    print("Generate API Response:")
    print(result)
