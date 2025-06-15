import os
import time
import numpy as np
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
from scipy.spatial.distance import cosine
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables from .env
load_dotenv()

# Initialize OpenAI client
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL")  # Optional: if using proxy like ai-proxy
)

# Initialize FastAPI app
app = FastAPI()

# --- RateLimiter class ---
class RateLimiter:
    def __init__(self, requests_per_minute=60, requests_per_second=2):
        self.requests_per_second = requests_per_second
        self.requests_per_minute = requests_per_minute
        self.request_times = []
        self.last_request_time = 0

    def wait_if_needed(self):
        current_time = time.time()

        # Per-second limit
        time_since_last = current_time - self.last_request_time
        if time_since_last < (1.0 / self.requests_per_second):
            time.sleep((1.0 / self.requests_per_second) - time_since_last)

        # Per-minute limit
        self.request_times = [t for t in self.request_times if current_time - t < 60]
        if len(self.request_times) >= self.requests_per_minute:
            wait_time = 60 - (current_time - min(self.request_times))
            print(f"[RateLimiter] Waiting {wait_time:.2f}s due to per-minute limit.")
            time.sleep(wait_time)

        self.last_request_time = time.time()
        self.request_times.append(self.last_request_time)

# Create a single instance of RateLimiter
rate_limiter = RateLimiter()

# --- Load embedding data ---
data = np.load("embeddings_data.npz", allow_pickle=True)

print("Available keys:", data.files)
print("embeddings shape:", data["embeddings"].shape)

metadata = data["metadata"]
docs = data["docs"]
embeddings = data["embeddings"]

print("metadata[0]:", metadata[0])

# --- Request schema ---
class QueryRequest(BaseModel):
    query: str

# --- Function: embed query ---
def embed_query(text: str) -> List[float]:
    print(f"Embedding query: {text}")
    rate_limiter.wait_if_needed()
    response = client.embeddings.create(
        input=[text],
        model="text-embedding-3-small"
    )
    return response.data[0].embedding

# --- Function: retrieve top-k ---
def retrieve(query_embedding, k=3):
    scores = [1 - cosine(query_embedding, doc_embedding) for doc_embedding in embeddings]
    top_k_indices = np.argsort(scores)[-k:][::-1]
    return [docs[i] for i in top_k_indices]

# --- Function: generate answer ---
def generate_answer(context_chunks, query):
    context_text = "\n\n".join(context_chunks)
    system_prompt = "You are a helpful assistant answering questions using course and forum content."
    user_prompt = f"Answer the question based on the following:\n\n{context_text}\n\nQuestion: {query}"

    print("Generating answer from context...")
    rate_limiter.wait_if_needed()
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    )
    return response.choices[0].message.content

# --- Endpoint ---
@app.post("/answer")
async def answer(query: QueryRequest):
    print("Received query:", query.query)
    query_embedding = embed_query(query.query)
    top_chunks = retrieve(query_embedding)
    answer_text = generate_answer(top_chunks, query.query)
    return {"answer": answer_text}

# For Vercel deployment
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
