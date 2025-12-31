# chatbot/clients.py
from __future__ import annotations
import os
import numpy as np
import faiss
from dotenv import load_dotenv
from openai import OpenAI
from google import genai

load_dotenv()

class Embedder:
    def __init__(self, model: str = "text-embedding-3-small"):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = model

    def embed(self, text: str) -> np.ndarray:
        res = self.client.embeddings.create(model=self.model, input=[text])
        v = np.array(res.data[0].embedding, dtype="float32").reshape(1, -1)
        faiss.normalize_L2(v)
        return v

class GeminiChat:
    def __init__(self):
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
