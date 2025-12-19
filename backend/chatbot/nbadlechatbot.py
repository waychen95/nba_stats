import os
import faiss
import numpy as np
import pickle
from dotenv import load_dotenv
from config import PROMPT_TEMPLATE
from openai import OpenAI
from google import genai

load_dotenv()

class NBAdleChatbot:
    
    def __init__(self, prompt_template):
        self.prompt_template = prompt_template
        self.load_embedding_model()
        self.load_faiss()
        self.load_chat_model()

    def load_chat_model(self):
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        print("Chat model loaded.")

    def load_faiss(self, index_path='players.index'):
        self.index = faiss.read_index(index_path)
        with open("players_texts.pkl", "rb") as f:
            self.texts = pickle.load(f)
        print("FAISS index and texts loaded.")

    def load_embedding_model(self):
        self.embedding = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        print("Embedding model loaded.")

    def embed_query(self, query: str):
        response = self.embedding.embeddings.create(
            model="text-embedding-3-small",
            input=[query]
        )
        query_vector = np.array(response.data[0].embedding).astype("float32")
        return query_vector
    
    def retrieve_similar_chunks(self, query: str, top_k: int = 3):
        # Embed the query
        query_vector = self.embed_query(query)

        # Search for similar chunks
        D, I = self.index.search(np.array([query_vector]), top_k)

        similar_texts = [self.texts[i] for i in I[0] if i < len(self.texts)]
        return similar_texts
    
    def generate_prompt(self, context: str, question: str) -> str:
        return self.prompt_template.format(context=context, question=question)
    
    def answer_question(self, question: str) -> str:
        similar_chunks = self.retrieve_similar_chunks(question, top_k=3)
        similar_chunks = list(dict.fromkeys(similar_chunks))
        context = "\n\n".join(similar_chunks)
        prompt = self.generate_prompt(context, question)
        print(prompt)

        response = self.client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config={
                "max_output_tokens": 2000,
                "temperature": 0.2
            }
        )

        return response.text.strip()
    
    def chat(self):
        print("Welcome to the NBAdle Chatbot! Ask me anything about NBA statistics.")
        while True:
            user_input = input("You: ")
            if user_input.lower() in ['exit', 'quit']:
                print("Goodbye!")
                break
            answer = self.answer_question(user_input)
            print(f"NBAdle: {answer}\n")

if __name__ == "__main__":
    chatbot = NBAdleChatbot(prompt_template=PROMPT_TEMPLATE)
    chatbot.chat()