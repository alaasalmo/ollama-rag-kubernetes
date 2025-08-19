from langchain.chains import RetrievalQA
from langchain_community.llms import Ollama
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import Chroma
from chromadb import HttpClient

# Setup remote Chroma client
client = HttpClient(host="127.0.0.1", port=8000)

# Embeddings (embedding model)
embeddings = OllamaEmbeddings(model="llama3", base_url="http://127.0.0.1:11434")

# Vectorstore
vectorstore = Chroma(client=client, collection_name="my_docs", embedding_function=embeddings)


docs = [
    "The Eiffel Tower is located in Paris, France.",
    "The Great Wall of China is over 13,000 miles long.",
    "Canada is located in North America and its capital is Ottawa."
]
vectorstore.add_texts(docs)


# LLM for generation
llm = Ollama(model="llama3", base_url="http://127.0.0.1:11434")

# Define the chain
qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    retriever=vectorstore.as_retriever(),
    chain_type="stuff"
)

# Use `.invoke()` instead of `.run()`
query = "Where is Canada map location?"

result = qa_chain.invoke({"query": query})  # returns dict with 'result' key
answer = result["result"]

print("Q:", query)
print("A:", answer)