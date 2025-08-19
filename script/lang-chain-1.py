#from langchain_community.llms import Ollama

### Create Ollama instance (change model if you want)
##llm = Ollama(model="llama3")

#llm = Ollama(
#    model="llama3",
#    base_url="http://localhost:11434/"
#)

### Ask a simple question
#question = "What is the capital of France?"
#answer = llm.invoke(question)

#print("Q:", question)
#print("A:", answer)



from langchain_community.llms import Ollama
from langchain.prompts import PromptTemplate

llm = Ollama(
    model="llama3",
    base_url="http://localhost:11434/"
)

# Create a prompt template with 'country' as the topic
prompt = PromptTemplate(
    input_variables=["country"],
    template="What is the capital of {country}?"
)

# Format the prompt with your country
formatted_prompt = prompt.format(country="France")
answer = llm.invoke(formatted_prompt)

print("Prompt:", formatted_prompt)
print("Answer:", answer)
