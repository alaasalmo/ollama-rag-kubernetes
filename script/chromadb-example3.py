from chromadb import HttpClient
from chromadb.config import Settings
from ollama import embeddings as ollama_embeddings
import requests
import numpy as np
import json


# --- Step 1: Define custom embedding_function ---
class OllamaEmbeddingFunction:
    #def __init__(self, model_name="nomic-embed-text", server_url="http://localhost:11434"):
    def __init__(self, model_name="nomic-embed-text", server_url="http://ollama-service-internal:11434"):
        self.model_name = model_name
        self.server_url = server_url

    def __call__(self, input: list[str]) -> list[list[float]]:
        embeddings = []
        for text in input:
            response = requests.post(
                f"{self.server_url}/api/embeddings",
                json={"model": self.model_name, "prompt": text},
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            embeddings.append(response.json()["embedding"])
        return np.array(embeddings, dtype=np.float32)

    def name(self):
        return f"ollama-{self.model_name}"

# --- Step 2: Initialize ChromaDB client ---
#client = HttpClient(host="localhost", port=8000)
client = HttpClient(host="chromadb-service-internal", port=8000)

# --- Step 3: Setup collection with embedding_function ---
embedding_function = OllamaEmbeddingFunction(model_name="llama3")
collection = client.get_or_create_collection(
    name="ollama-embedding-demo",
    embedding_function=embedding_function
)

# --- Step 4: Add documents ---
documents = [
    "The Earth revolves around the Sun.",
    "Water boils at 100 degrees Celsius.",
    "Python is a popular programming language."
]
ids = ["doc1", "doc2", "doc3"]
collection.add(documents=documents, ids=ids)

# --- Step 5: Query with embedding_function auto-used ---
query = "What temperature does water boil at?"
results = collection.query(query_texts=[query], n_results=2)

# --- Step 6: Print top results and collect context ---
print("\n🔍 Top Results:")
top_docs = []
for doc, dist in zip(results["documents"][0], results["distances"][0]):
    print(f"- {doc} (score: {dist:.4f})")
    top_docs.append(doc)

# --- Step 7: Chat-based answer generation using LLM ---

def generate_answer_with_chat(model: str, system_prompt: str, user_question: str, context_docs: list[str]) -> str:
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"{user_question}\n\nContext:\n" + "\n".join(context_docs)}
    ]

    response = requests.post(
        "http://ollama-service-internal:11434/api/chat",
        json={"model": model, "messages": messages},
        headers={"Content-Type": "application/json"},
        stream=True  # Required to handle Ollama's streaming output
    )
    response.raise_for_status()

    output = ""
    for line in response.iter_lines():
        if line:
            data = json.loads(line.decode('utf-8'))  # ✅ Use json.loads directly
            delta = data.get("message", {}).get("content", "")
            output += delta
    return output

# --- Step 8: Call LLM with chat ---
system_prompt = "You are a helpful assistant who answers questions based only on the provided context."
llm_answer = generate_answer_with_chat(
    model="llama3",
    system_prompt=system_prompt,
    user_question=query,
    context_docs=top_docs
)

print("\n🧠 LLM Answer:\n", llm_answer)
