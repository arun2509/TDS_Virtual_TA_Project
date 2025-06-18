import os
import time
import json
import numpy as np
from pathlib import Path
from tqdm import tqdm
from dotenv import load_dotenv
from openai import OpenAI
from typing import List
import tiktoken

# === Load env ===
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
api_base = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
client = OpenAI(api_key=api_key, base_url=api_base)

# === Tokenizer for OpenAI ===
encoding = tiktoken.encoding_for_model("text-embedding-3-small")

def count_tokens(text: str) -> int:
    return len(encoding.encode(text))

# === Safe chunking ===
def split_markdown(text: str, chunk_size: int = 1500, chunk_overlap: int = 50) -> List[str]:
    tokens = encoding.encode(text)
    chunks = []
    start = 0
    while start < len(tokens):
        end = start + chunk_size
        chunk = tokens[start:end]
        chunks.append(encoding.decode(chunk))
        start += chunk_size - chunk_overlap
    return chunks

# === Retry wrapper ===
def get_embedding(text: str, max_retries=3) -> List[float]:
    for attempt in range(max_retries):
        try:
            if attempt > 0:
                time.sleep(2 ** attempt)
            response = client.embeddings.create(
                model="text-embedding-3-small",
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"⚠️ Error: {e}. Retrying in {2**attempt}s...")
            if attempt == max_retries - 1:
                raise

# === Load markdown files ===
FOLDER_PATHS = ["Course_content_jan_2025", "topics_md"]
OUTPUT_FILE = "embeddings_data.npz"

print("📚 Collecting markdown files...")
all_files = []
for folder in FOLDER_PATHS:
    all_files += list(Path(folder).rglob("*.md"))
print(f"📄 Found {len(all_files)} markdown files")

# === Chunking ===
chunks = []
metadata = []
doc_map = {}

for file in all_files:
    with open(file, "r", encoding="utf-8") as f:
        content = f.read()
    file_chunks = split_markdown(content)
    for i, chunk in enumerate(file_chunks):
        chunks.append(chunk)
        metadata.append({
            "source": str(file),
            "chunk_id": i
        })
    doc_map[str(file)] = content

print(f"🧩 Total chunks to embed: {len(chunks)}")

# === Embed with progress bar ===
embeddings = []
for chunk in tqdm(chunks, desc="🔢 Embedding Chunks"):
    emb = get_embedding(chunk)
    embeddings.append(emb)

# === Save ===
docs = [doc_map[m["source"]] for m in metadata]
np.savez_compressed(OUTPUT_FILE,
                    embeddings=np.array(embeddings, dtype=np.float32),
                    metadata=metadata,
                    docs=docs)

print(f"✅ Done! Saved to {OUTPUT_FILE}")
