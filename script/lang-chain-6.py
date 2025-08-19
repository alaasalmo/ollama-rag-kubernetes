from langchain_community.chat_models import ChatOllama
from langchain.prompts import ChatPromptTemplate

# 1️⃣ Create the ChatOllama LLM
llm = ChatOllama(
    model="llama3",                     # The model you have in Ollama
    base_url="http://127.0.0.1:11434",  # Ollama server
    temperature=0.2
)

# 2️⃣ Create a ChatPromptTemplate
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a knowledgeable assistant that answers questions about countries."),
    ("human", "Tell me three interesting facts about {country}.")
])

# 3️⃣ Format the prompt with variables
final_prompt = prompt.format_messages(country="Canada")

# 4️⃣ Invoke the model
response = llm.invoke(final_prompt)

# 5️⃣ Print response
print(response.content)
