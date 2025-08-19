import json
from typing import List, Dict
from langchain_community.chat_models import ChatOllama

# 1️⃣ Create Ollama LLM
llm = ChatOllama(
    model="llama3",
    base_url="http://127.0.0.1:11434",
    temperature=0
)

# 2️⃣ Function to call Ollama chat
def call_ollama_chat(messages):
    response = llm.invoke(messages)
    return response.content.strip()

# 3️⃣ Rerank function
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
                c = candidates[idx].copy()
                c["score"] = score
                scored.append(c)
        return sorted(scored, key=lambda x: x["score"], reverse=True)
    except Exception:
        return candidates  # fallback

# 4️⃣ Example usage
docs = [
    {"text": "Ottawa is the capital of Canada and is located in Ontario."},
    {"text": "Toronto is a major Canadian city located in Ontario."},
    {"text": "Canada shares the longest undefended border in the world with the United States."}
]

query = "What is the capital of Canada?"
ranked = rerank(query, docs)

print("📊 Ranked Results:")
for r in ranked:
    print(f"Score: {r['score']} | Text: {r['text']}")
