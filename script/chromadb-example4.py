import requests
import chromadb
from chromadb.utils import embedding_functions
from chromadb import HttpClient

# --- Step 1: Create a custom embedding function for Ollama ---
class OllamaEmbeddingFunction(embedding_functions.EmbeddingFunction):
    def __init__(self, model_name="llama3", server_url="http://ollama-service-internal:11434"):
    #def __init__(self, model_name="llama3", server_url="http://127.0.0.1:11434"):

        self.model_name = model_name
        self.server_url = server_url

    def __call__(self, texts):
        embeddings = []
        for text in texts:
            response = requests.post(
                f"{self.server_url}/api/embeddings",
                json={"model": self.model_name, "prompt": text}
            )
            response.raise_for_status()
            data = response.json()
            embeddings.append(data["embedding"])
        return embeddings

# --- Step 2: Create ChromaDB client ---
#client = chromadb.Client()
#client = HttpClient(host="localhost", port=8000)
client = HttpClient(host="chromadb-service-internal", port=8000)


# --- Step 3: Initialize our Ollama embedding function ---
ollama_ef = OllamaEmbeddingFunction(
    model_name="llama3", 
    #server_url="http://127.0.0.1:11434"  # Change to your Ollama IP:Port
    server_url="http://ollama-service-internal:11434"
)   

# --- Step 4: Create collection ---
collection = client.get_or_create_collection(
    name="ollama_collection",
    embedding_function=ollama_ef
)

# --- Step 5: Add documents ---
collection.add(
    documents=[
        "LangChain is a framework for developing applications with LLMs.",
        "ChromaDB is an open-source vector database for storing embeddings."
    ],
    ids=["doc1", "doc2"]
)

# --- Step 6: Query the database ---
results = collection.query(
    query_texts=["What is LangChain?"],
    n_results=2
)

print(results)
