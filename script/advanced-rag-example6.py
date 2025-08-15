import requests
import json
from typing import List, Dict
from chromadb import HttpClient
import requests
from typing import List, Dict


#OLLAMA_API = "http://localhost:11434"
OLLAMA_API = "http://ollama-service-internal:11434"
#CHROMA_DB = "127.0.0.1"
CHROMA_DB = "chromadb-service-internal"
CHAT_MODEL = "llama3"

# Step 1: Call Ollama embedding API
def embed_texts(texts: List[str], model="llama3") -> List[List[float]]:
    embeddings = []
    for text in texts:
        response = requests.post(
            f"{OLLAMA_API}/api/embeddings",  # or your internal service URL
            json={"model": model, "prompt": text}
        )
        response.raise_for_status()
        data = response.json()
        # Ollama's embedding response key might be 'embedding' or 'embeddings', adjust if needed
        embedding = data.get("embedding") or data.get("embeddings")
        if embedding is None:
            raise ValueError("Embedding not found in Ollama response")
        embeddings.append(embedding)
    return embeddings

# Step 2: Call Ollama chat API
def call_ollama_chat(messages: List[Dict]) -> str:
    payload = {
        "model": CHAT_MODEL,
        "messages": messages,
        "stream": False  # Important: so .json() works without streaming parser
    }
    resp = requests.post(f"{OLLAMA_API}/api/chat", json=payload)
    resp.raise_for_status()
    data = resp.json()
    print("Response JSON:", data)
    # Ollama's /api/chat puts the content here:
    return data["message"]["content"]

# Step 3: Chunk text (simple no-overlap)
def chunk_texts(texts: List[str], chunk_size=500) -> List[Dict]:
    chunks = []
    chunk_id = 0
    for doc_id, text in enumerate(texts):
        for start in range(0, len(text), chunk_size):
            chunk = text[start:start+chunk_size]
            chunks.append({
                "id": f"doc{doc_id}_chunk{chunk_id}",
                "text": chunk,
                "metadata": {"doc_id": doc_id, "chunk_id": chunk_id}
            })
            chunk_id += 1
    return chunks

# Step 4: Initialize Chroma client
def get_chroma_client():
    client = HttpClient(host=f"{CHROMA_DB}", port=8000)  # Replace with your server IP
    return client   

# Step 5: Upsert chunks + embeddings
def upsert_chunks(client, chunks: List[Dict], embeddings: List[List[float]]):
    collection_name = "rag_collection"
    if collection_name in [c.name for c in client.list_collections()]:
        collection = client.get_collection(collection_name)
    else:
        collection = client.create_collection(name=collection_name, embedding_function=None)

    ids = [c["id"] for c in chunks]
    docs = [c["text"] for c in chunks]
    metas = [c["metadata"] for c in chunks]
    collection.upsert(ids=ids, embeddings=embeddings, documents=docs, metadatas=metas)

# Step 6: Query rewriting 
def rewrite_query(query: str) -> str:
    messages = [
        {"role": "system", "content": "You are a query rewriting assistant. Make the query clearer and more specific."},
        {"role": "user", "content": query},
    ]

    rewritten = call_ollama_chat(messages)
    return rewritten.strip()


# Step 7: Retrieve top-k chunks
def retrieve(client, query: str, top_k=5) -> List[Dict]:
    collection = client.get_collection("rag_collection")
    q_emb = embed_texts([query])[0]
    results = collection.query(query_embeddings=[q_emb], n_results=top_k, include=["documents", "metadatas"])
    hits = []
    for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
        hits.append({"text": doc, "metadata": meta})
    return hits

# Step 8 Re-rank retrieved chunks 
def rerank(query: str, candidates: List[Dict]) -> List[Dict]:
    prompt = f"""You are a relevance scorer. Rate each passage 1 (irrelevant) to 10 (highly relevant) for this query:

{query}

Passages:
"""
    for i, c in enumerate(candidates):
        snippet = c["text"][:200].replace("\n", " ")
        prompt += f"\n[{i}] {snippet}..."

    prompt += '\n\nReturn JSON list of objects [{"score": <int>, "index": <int>}].'

    messages = [
        {"role": "system", "content": "You are a helpful assistant that scores relevance."},
        {"role": "user", "content": prompt},
    ]

    resp = call_ollama_chat(messages)
    try:
        scores = json.loads(resp)
        scored = []
        for s in scores:
            idx = s.get("index")
            score = s.get("score")
            if idx is not None and 0 <= idx < len(candidates):
                c = candidates[idx]
                c["score"] = score
                scored.append(c)
        return sorted(scored, key=lambda x: x["score"], reverse=True)
    except Exception:
        return candidates  # fallback

# Step 9: Summarize context
def summarize_context(chunks: List[Dict]) -> str:
    combined_text = "\n\n".join([c["text"] for c in chunks])
    prompt = f"""Summarize the following context concisely:

{combined_text}

Summary:"""
    messages = [
        {"role": "system", "content": "You are a helpful assistant that summarizes text."},
        {"role": "user", "content": prompt},
    ]
    summary = call_ollama_chat(messages)
    return summary.strip()

# Step 10: Generate final answer
def generate_answer(query: str, summary: str, chunks: List[Dict]) -> str:
    sources = ", ".join([f"chunk {c['metadata']['chunk_id']}" for c in chunks])
    prompt = f"""You are a helpful assistant. Use the summary and context to answer the question. If you don't know, say so.

Summary:
{summary}

Question:
{query}

Answer (include SOURCES: {sources}):"""
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": prompt},
    ]
    answer = call_ollama_chat(messages)
    return answer.strip()

# --- Main ---
def main():
    # Example docs
    docs = [
        "Ollama is a local LLM server that supports embeddings and chat models.",
        "Chroma is a vector database designed for embedding search and retrieval.",
        "RAG stands for Retrieval-Augmented Generation, combining search with LLMs."
    ]

    chunks = chunk_texts(docs)
    embeddings = embed_texts([c["text"] for c in chunks])

    client = get_chroma_client()
    upsert_chunks(client, chunks, embeddings)

    user_query = "Explain advanced RAG."

    print("Rewriting query...")
    rewritten_query = rewrite_query(user_query)
    print("Rewritten query:", rewritten_query)

    print("Retrieving documents...")
    retrieved = retrieve(client, rewritten_query)

    print("Re-ranking...")
    reranked = rerank(rewritten_query, retrieved)

    print("Summarizing context...")
    summary = summarize_context(reranked)

    print("Generating final answer...")
    answer = generate_answer(rewritten_query, summary, reranked)

    print("\n=== FINAL ANSWER ===\n")
    print(answer)

if __name__ == "__main__":
    main()
