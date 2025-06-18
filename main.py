import os
import time
import numpy as np
from fastapi import FastAPI, Request
from openai import OpenAI
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import List
from scipy.spatial.distance import cosine
from PIL import Image
import pytesseract

# Load API keys
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"), base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"))

# FastAPI app
app = FastAPI()

# Rate Limiter
class RateLimiter:
    def __init__(self, requests_per_minute=60, requests_per_second=2):
        self.requests_per_minute = requests_per_minute
        self.requests_per_second = requests_per_second
        self.request_times = []
        self.last_request_time = 0

    def wait_if_needed(self):
        current_time = time.time()

        if (current_time - self.last_request_time) < (1.0 / self.requests_per_second):
            time.sleep((1.0 / self.requests_per_second) - (current_time - self.last_request_time))

        self.request_times = [t for t in self.request_times if current_time - t < 60]
        if len(self.request_times) >= self.requests_per_minute:
            time.sleep(60 - (current_time - self.request_times[0]))

        self.request_times.append(time.time())
        self.last_request_time = time.time()

rate_limiter = RateLimiter(requests_per_minute=5, requests_per_second=2)

# ---------------------- Load Embeddings ----------------------
data = np.load("embeddings_data.npz", allow_pickle=True)
docs = data["docs"]
embeddings = data["embeddings"]
metadata = data["metadata"]

def get_embedding(text: str) -> List[float]:
    """Get OpenAI embedding for a given text"""
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return response.data[0].embedding

def most_similar_chunks(query_embedding: List[float], top_k: int = 10) -> List[str]:
    """Return top_k most similar chunks based on cosine similarity"""
    sims = [1 - cosine(query_embedding, emb) for emb in embeddings]
    top_indices = np.argsort(sims)[-top_k:][::-1]
    return [docs[i] for i in top_indices]

def generate_response(question: str, context: str) -> str:
    """Generate response using OpenAI GPT-4-turbo with a strict system prompt"""
    system_prompt = (
        "You are a helpful teaching assistant. Use the following context to answer the question. "
        "Do not make up information, but feel free to use your reasoning skills to interpret the context.\n\n"
        "* Use **Markdown** formatting.\n"
        "* Prefer code blocks and bullet points if helpful.\n"
        "* If the context is completely unrelated or empty, reply with:\n"
        "```\nI don't know\n```"
    )

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion:\n{question}"}
        ],
        temperature=0.3,
        max_tokens=512
    )
    return response.choices[0].message.content.strip()

def extract_image_text(image_path: str) -> str:
    """Extract text from image using Tesseract OCR"""
    try:
        image = Image.open(image_path)
        return pytesseract.image_to_string(image)
    except Exception as e:
        return ""

@app.post("/api/")
async def api_answer(request: Request):
    try:
        data = await request.json()
        question = data.get("question", "")
        image_uri = data.get("image", "")

        if not question.strip():
            return {"error": "Question cannot be empty."}

        # Append OCR from image if provided
        image_text = ""
        if image_uri.startswith("file://"):
            image_path = image_uri[7:]  # strip file://
            if os.path.exists(image_path):
                image_text = extract_image_text(image_path)
        
        # Include image text as part of the question
        if image_text:
            question += f"\n\n[Image OCR Content]\n{image_text}"

        query_embedding = get_embedding(question)
        top_chunks = most_similar_chunks(query_embedding)
        context = "\n\n".join(top_chunks)
        answer = generate_response(question, context)

        return {
            "question": question,
            "answer": answer,
            "links": [],  # Optional: include if you extract or generate links
            "top_chunks": top_chunks
        }
    
    except Exception as e:
        return {"error": str(e)}

# For local dev run
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=10000)
