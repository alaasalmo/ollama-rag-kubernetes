from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.llms import Ollama
from langchain_community.vectorstores import Chroma
from langchain.chains import RetrievalQA
from chromadb import HttpClient

# 1️⃣ Connect to remote ChromaDB HTTP API
client = HttpClient(host="127.0.0.1", port=8000)  # Replace with your server IP

# 2️⃣ Create Ollama embedding function (embedding model)
embeddings = OllamaEmbeddings(
    model="llama3",           # Embedding model, not llama3
    base_url="http://127.0.0.1:11434"  # Ollama server URL
)

# 3️⃣ Create or get remote Chroma collection
vectorstore = Chroma(
    client=client,
    collection_name="my_docs",
    embedding_function=embeddings
)

# 4️⃣ Add documents to the vector store (only if you haven't already)
docs = [
    "The Eiffel Tower is located in Paris, France.",
    "The Great Wall of China is over 13,000 miles long.",
    "Capital of Canada is Ottawa."
]
vectorstore.add_texts(docs)

# 5️⃣ Create the llama3 LLM for answer generation
llm = Ollama(
    model="llama3",
    base_url="http://127.0.0.1:11434"
)

# 6️⃣ Build RetrievalQA chain with LangChain
qa = RetrievalQA.from_chain_type(
    llm=llm,
    retriever=vectorstore.as_retriever(),
    chain_type="stuff"
)

# 7️⃣ Ask a question
# query = "Where is the Eiffel Tower located?"
query = "Where is capital of Canada?"
#answer = qa.run(query)
answer = qa.invoke({"query": query})["result"]


print("Q:", query)
print("A:", answer)
