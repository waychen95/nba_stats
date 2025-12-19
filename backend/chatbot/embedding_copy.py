import pandas as pd
import faiss
import numpy as np
import pickle
import os
from dotenv import load_dotenv
import tiktoken
from openai import OpenAI

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Load the text data
with open('embedding_data.txt', 'r', encoding='utf-8') as f:
    data = f.read()

# Initialize tokenizer for counting tokens
encoding = tiktoken.get_encoding("cl100k_base")

def chunk_text_with_overlap(text, max_tokens=500, overlap_tokens=50):
    """
    Splits text into chunks of roughly max_tokens tokens with a small overlap.
    Returns a list of strings.
    """
    words = text.split()
    chunks = []
    start_idx = 0
    while start_idx < len(words):
        current_chunk = []
        current_tokens = 0
        idx = start_idx
        while idx < len(words):
            word_tokens = len(encoding.encode(words[idx]))
            if current_tokens + word_tokens > max_tokens:
                break
            current_chunk.append(words[idx])
            current_tokens += word_tokens
            idx += 1
        chunks.append(" ".join(current_chunk))
        # move start index back by overlap
        start_idx = max(start_idx + len(current_chunk) - overlap_tokens, start_idx + 1)
    return chunks

# Split text into chunks with overlap
texts = chunk_text_with_overlap(data, max_tokens=500, overlap_tokens=50)

# Generate embeddings in batches
batch_size = 100
vectors = []

for i in range(0, len(texts), batch_size):
    batch = texts[i:i+batch_size]
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=batch
    )
    vectors.extend([e.embedding for e in response.data])

# Convert embeddings to NumPy array
vectors = np.array(vectors).astype("float32")

# Create a FAISS index and add vectors
index = faiss.IndexFlatL2(vectors.shape[1])
index.add(vectors)

# Save the FAISS index
faiss.write_index(index, "players.index")

# Save the text chunks for retrieval
with open("players_texts.pkl", "wb") as f:
    pickle.dump(texts, f)

print(f"Done: {len(texts)} chunks embedded and saved with overlap.")
