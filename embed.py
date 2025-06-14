import os
import time
import numpy as np
import tiktoken
import openai
from dotenv import load_dotenv

# Load .env file containing OPENAI_API_KEY
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
openai.api_base = os.getenv("OPENAI_BASE_URL")

# Rate Limiter class
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
        self.request_times = [
            t for t in self.request_times if current_time - t < 60
        ]
        if len(self.request_times) >= self.requests_per_minute:
            wait_time = 60 - (current_time - min(self.request_times))
            if wait_time > 0:
                time.sleep(wait_time)

        self.last_request_time = time.time()
        self.request_times.append(self.last_request_time)

# Initialize rate limiter
ratelimiter = RateLimiter(requests_per_minute=60, requests_per_second=2)

# === CONFIGURATION ===
MAX_TOKENS = 500
OVERLAP = 100
DATA_DIRS = ["Course_content_jan_2025", "topics_md"]

# Tokenizer
tokenizer = tiktoken.get_encoding("cl100k_base")

def chunk_markdown_file(path):
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()

    tokens = tokenizer.encode(text)
    chunks = []
    i = 0
    while i < len(tokens):
        chunk = tokens[i:i + MAX_TOKENS]
        decoded = tokenizer.decode(chunk)
        chunks.append(decoded)
        i += MAX_TOKENS - OVERLAP

    return chunks

all_chunks = []
metadata = []

print(f"🧠 Processing Markdown files from: {', '.join(DATA_DIRS)}...")
for dir_name in DATA_DIRS:
    for fname in os.listdir(dir_name):
        if not fname.endswith(".md"):
            continue
        path = os.path.join(dir_name, fname)
        chunks = chunk_markdown_file(path)
        for chunk in chunks:
            all_chunks.append(chunk)
            metadata.append({"source": fname})

print(f"📄 Total chunks to embed: {len(all_chunks)}")

# Compute embeddings with rate limiting
embeddings = []
for i, chunk in enumerate(all_chunks):
    ratelimiter.wait_if_needed()
    print(f"🔢 Embedding chunk {i + 1}/{len(all_chunks)}")
    response = openai.embeddings.create(
        model="text-embedding-3-small",
        input=chunk
    )
    embeddings.append(response.data[0].embedding)

# Save embeddings and metadata
np.savez_compressed("embeddings_data.npz", embeddings=np.array(embeddings), metadata=metadata)
print("✅ All embeddings saved to embeddings_data.npz")

