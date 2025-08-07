#from chromadb import Client
from chromadb import HttpClient
from chromadb.config import Settings
from ollama import embeddings as ollama_embeddings
import requests
import numpy as np

# --- Step 1: Define custom embedding_function ---

class OllamaEmbeddingFunction:
    def __init__(self, model_name="nomic-embed-text", server_url="http://ollama-service-internal:11434"):
    #def __init__(self, model_name="nomic-embed-text", server_url="http://localhost:11434"):
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
        return np.array(embeddings, dtype=np.float32)  # ✅ Important

    def name(self):
        return f"ollama-{self.model_name}"

    

# --- Step 2: Initialize ChromaDB client ---
#client = Client(Settings(anonymized_telemetry=False))
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

# --- Step 6: Print results ---
print("\n🔍 Top Results:")
for doc, dist in zip(results["documents"][0], results["distances"][0]):
    print(f"- {doc} (score: {dist:.4f})")
