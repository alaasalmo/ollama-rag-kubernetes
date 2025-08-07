import os
import numpy as np
from uuid import uuid4
from ollama import embeddings
import chromadb
from chromadb.config import Settings
import requests

# --- Configuration ---
FILE_PATH = "sample.txt"
CHUNK_SIZE = 300
OVERLAP = 50
MODEL_NAME = "llama3"
CHROMA_PATH = "chroma_store"

# --- Step 1: Read and Chunk File ---
def read_and_chunk_file(path, chunk_size=300, overlap=50):
    row = 0
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read()
        chunks = []
        ids=[]
        start = 0
        i=0
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            chunks.append(chunk)
            start += chunk_size - overlap
            ids.append(f"row{row}_chunk{i}")
            i += 1
        row += 1
    return chunks,ids

# --- Step 2: Use Ollama to Embed Chunks ---
def get_ollama_embeddings(texts, model="llama3"):
    embeddings = []
    for text in texts:
        response = requests.post(
            "http://ollama-service-internal:11434/api/embeddings",
            #"http://localhost:11434/api/embeddings",
            json={"model": model, "prompt": text}
        )
        response.raise_for_status()
        embeddings.append(response.json()["embedding"])
    return embeddings

# --- Step 3: Save to ChromaDB ---
def save_to_chromadb(chunks,ids, embeddings_list, collection_name="ollama_docs2"):
    client = chromadb.HttpClient(host="chromadb-service-internal", port=8000)
    #client = chromadb.HttpClient(host="localhost", port=8000)
    collection = client.get_or_create_collection(collection_name)
    collection.add(documents=chunks,ids=ids,embeddings=embeddings_list)


# --- Step 4: Get Result from query ---
def get_query(query, collection_name="ollama_docs",n_s=3):
    client = chromadb.HttpClient(host="chromadb-service-internal", port=8000)
    #client = chromadb.HttpClient(host="localhost", port=8000)
    query_embedding = get_ollama_embeddings([query])
    collection = client.get_or_create_collection(collection_name)
    results = collection.query(query_embeddings=query_embedding,n_results=n_s)
    return results 

    #collection.add(documents=chunks,ids=ids,embeddings=embeddings_list)

# --- Main Execution ---
if __name__ == "__main__":
    # 1. Read and chunk the file
    chunks,ids = read_and_chunk_file(FILE_PATH, CHUNK_SIZE, OVERLAP)
    print(f"Chunked into {len(chunks)} pieces.")
    print(f"ids length" + str(len(ids)))

    # 2. Generate embeddings using Ollama
    embeddings_list = get_ollama_embeddings(chunks, model=MODEL_NAME)

    # 3. Save embeddings (optional)
    np.save("ollama_embeddings.npy", embeddings_list)
    print("Embeddings saved to ollama_embeddings.npy")

    # 4. Save to ChromaDB
    save_to_chromadb(chunks, ids,embeddings_list)

    # 5. Show preview
    for i, chunk in enumerate(chunks[:2]):
        print(f"\nChunk {i}:\n{chunk}\nEmbedding preview:\n{embeddings_list[i][:5]}")

    # 6 . Query example
    query = "What is Ethical considerations are important as AI?"
    #query_embedding = get_ollama_embeddings([query])
    results=get_query(query, collection_name="ollama_docs",n_s=3)
    print("\n🔍 Top Results:")
    for doc, dist in zip(results["documents"][0], results["distances"][0]):
        print(f"- {doc} (score: {dist:.4f})")