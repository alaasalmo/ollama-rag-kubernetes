import requests
from bs4 import BeautifulSoup
from langchain.text_splitter import RecursiveCharacterTextSplitter
import re

def fetch_and_clean_text(url: str) -> str:
    # Fetch raw HTML
    response = requests.get(url)
    response.raise_for_status()
    html = response.text

    # Parse HTML and extract visible text
    soup = BeautifulSoup(html, "html.parser")

    # Remove script and style elements
    for tag in soup(["script", "style"]):
        tag.decompose()

    text = soup.get_text(separator=" ")

    # Clean whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text

def split_text(text: str, chunk_size=500, chunk_overlap=100):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    return splitter.split_text(text)

# Usage
url = "https://en.wikipedia.org/wiki/Canada"
cleaned_text = fetch_and_clean_text(url)
chunks = split_text(cleaned_text)

# Show first few chunks
for i, chunk in enumerate(chunks[:3]):
    print(f"--- Chunk {i+1} ---\n{chunk}\n")
