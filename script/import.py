import requests
import chromadb
import textwrap

# --- Step 1: Sample Documents ---
documents = [
    "Python is widely used in data science.",
    "Kubernetes manages containerized workloads.",
    "ChromaDB helps with fast vector searches."
]

# --- Step 2: Chunking Helper ---
def chunk_text(text, chunk_size=100):
    return textwrap.wrap(text, chunk_size)

chunks = []
ids = []
for i, doc in enumerate(documents):
    doc_chunks = chunk_text(doc)
    for j, chunk in enumerate(doc_chunks):
        chunks.append(chunk)
        ids.append(f"doc{i}_chunk{j}")

# --- Step 3: Embedding with Ollama ---
def embed_with_ollama(texts, model="llama3"):
    embeddings = []
    for text in texts:
        response = requests.post(
            "http://ollama-service-internal:11434/api/embeddings",
            json={"model": model, "prompt": text}
        )
        response.raise_for_status()
        embeddings.append(response.json()["embedding"])
    return embeddings

embeddings = embed_with_ollama(chunks)

# --- Step 4: Store in ChromaDB (HTTP client) ---
client = chromadb.HttpClient(host="chromadb-service-internal", port=8000)
collection = client.get_or_create_collection("ollama_rag")

collection.add(
    documents=chunks,
    ids=ids,
    embeddings=embeddings
)

print("✅ Chunks embedded & stored in ChromaDB")

query = "How do containers get managed?"
query_embedding = embed_with_ollama([query])

results = collection.query(
    query_embeddings=query_embedding,
    n_results=3
)

print("\n🔍 Top Results:")
for doc, dist in zip(results["documents"][0], results["distances"][0]):
    print(f"- {doc} (score: {dist:.4f})")