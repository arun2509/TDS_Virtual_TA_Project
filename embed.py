import os
import time
import numpy as np
import tiktoken
import openai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
openai.api_base = os.getenv("OPENAI_BASE_URL")

# === Rate Limiter ===
class RateLimiter:
    def __init__(self, requests_per_minute=60, requests_per_second=2):
        self.requests_per_second = requests_per_second
        self.requests_per_minute = requests_per_minute
        self.request_times = []
        self.last_request_time = 0

    def wait_if_needed(self):
        current_time = time.time()
        time_since_last = current_time - self.last_request_time

        if time_since_last < (1.0 / self.requests_per_second):
            time.sleep((1.0 / self.requests_per_second) - time_since_last)

        self.request_times = [t for t in self.request_times if current_time - t < 60]
        if len(self.request_times) >= self.requests_per_minute:
            wait_time = 60 - (current_time - min(self.request_times))
            if wait_time > 0:
                time.sleep(wait_time)

        self.last_request_time = time.time()
        self.request_times.append(self.last_request_time)

ratelimiter = RateLimiter()

# === CONFIG ===
MAX_TOKENS = 500
OVERLAP = 100
DATA_DIRS = ["Course_content_jan_2025", "topics_md"]
tokenizer = tiktoken.get_encoding("cl100k_base")

# === Chunking ===
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
doc_map = {}  # source file → full content

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

        # Save full file for later reconstruction
        with open(path, "r", encoding="utf-8") as f:
            doc_map[fname] = f.read()

print(f"📄 Total chunks to embed: {len(all_chunks)}")

# === Embed all chunks ===
embeddings = []
for i, chunk in enumerate(all_chunks):
    ratelimiter.wait_if_needed()
    print(f"🔢 Embedding chunk {i + 1}/{len(all_chunks)}")
    response = openai.embeddings.create(
        model="text-embedding-3-small",
        input=chunk
    )
    embeddings.append(response.data[0].embedding)

# === Rebuild docs list from metadata ===
docs = []
for m in metadata:
    source = m["source"]
    docs.append(doc_map.get(source, ""))  # fallback empty

# === Save compressed embeddings ===
np.savez_compressed("embeddings_data.npz",
                    embeddings=np.array(embeddings).astype(np.float32),
                    metadata=metadata,
                    docs=docs)

print("✅ All embeddings and docs saved to embeddings_data.npz (compressed)")
