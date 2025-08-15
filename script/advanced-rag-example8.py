import requests
import json
from typing import List, Dict
from chromadb import HttpClient

# Configuration
#OLLAMA_API = "http://localhost:11434"
OLLAMA_API = "http://ollama-service-internal:11434"
#CHROMA_DB = "127.0.0.1"
CHROMA_DB = "chromadb-service-internal"
CHAT_MODEL = "llama3"
EMBED_MODEL = "llama3"

# Step 1: Call Ollama embedding API
def embed_texts(texts: List[str], model=EMBED_MODEL) -> List[List[float]]:
    embeddings = []
    for text in texts:
        response = requests.post(
            f"{OLLAMA_API}/api/embeddings",
            json={"model": model, "prompt": text}
        )
        response.raise_for_status()
        data = response.json()
        embedding = data.get("embedding") or data.get("embeddings")
        if embedding is None:
            raise ValueError("Embedding not found in Ollama response")
        embeddings.append(embedding)
    return embeddings

# Step 2: Call Ollama chat API
def call_ollama_chat(messages: List[Dict]) -> str:
    payload = {"model": CHAT_MODEL, "messages": messages, "stream": False}
    resp = requests.post(f"{OLLAMA_API}/api/chat", json=payload)
    resp.raise_for_status()
    data = resp.json()
    return data["message"]["content"]

# Step 3: Chunk text
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
    client = HttpClient(host=CHROMA_DB, port=8000)
    return client

# Step 5 Upsert chunks + embeddings
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

# Step 6: Multi-query expansion
def expand_queries(user_query: str, n_variations=3) -> List[str]:
    prompt = f"""
You are an assistant that generates {n_variations} different, semantically diverse queries
based on the user query, preserving the intent. Return a JSON list of strings only.
User query: "{user_query}"
"""
    messages = [
        {"role": "system", "content": "You are a query expansion assistant."},
        {"role": "user", "content": prompt},
    ]
    resp = call_ollama_chat(messages)
    try:
        queries = json.loads(resp)
        if isinstance(queries, list):
            return [q.strip() for q in queries]
    except Exception:
        pass
    return [user_query]

# Step 7: Retrieve top-k chunks for multiple queries
def retrieve_multi(client, queries: List[str], top_k=5) -> List[Dict]:
    all_hits = []
    collection = client.get_collection("rag_collection")
    for q in queries:
        q_emb = embed_texts([q])[0]
        results = collection.query(
            query_embeddings=[q_emb],
            n_results=top_k,
            include=["documents", "metadatas"]
        )
        for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
            all_hits.append({"text": doc, "metadata": meta})
    # Deduplicate by text
    unique_hits = {h["text"]: h for h in all_hits}.values()
    return list(unique_hits)

# Step 8: Re-rank retrieved chunks
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
        return candidates

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
    return call_ollama_chat(messages).strip()

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
    return call_ollama_chat(messages).strip()

# ---------------- Main ----------------
def main():
    # Example documents
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

    print("Expanding queries...")
    queries = expand_queries(user_query, n_variations=3)
    print("Generated queries:", queries)

    print("Retrieving documents for all queries...")
    retrieved = retrieve_multi(client, queries)

    print("Re-ranking...")
    reranked = rerank(user_query, retrieved)

    print("Summarizing context...")
    summary = summarize_context(reranked)

    print("Generating final answer...")
    answer = generate_answer(user_query, summary, reranked)

    print("\n=== FINAL ANSWER ===\n")
    print(answer)

if __name__ == "__main__":
    main()
