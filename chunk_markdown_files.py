import os
import json
import re

# Configuration
dirs = ["Course_content_jan_2025", "topics_md"]
chunk_size = 500
overlap = 100
output_file = "chunks.jsonl"

def remove_image_tags(content):
    # Remove Markdown image links ![alt](image.png)
    content = re.sub(r'!\[.*?\]\(.*?\)', '', content)
    # Remove HTML <img> tags
    content = re.sub(r'<img[^>]*>', '', content)
    # Remove base64 image strings like data:image/png;base64,....
    content = re.sub(r'data:image/[^;]+;base64,[A-Za-z0-9+/=\s]+', '', content)
    return content

def chunk_text(text, size, overlap):
    chunks = []
    start = 0
    while start < len(text):
        end = start + size
        chunks.append(text[start:end])
        start += size - overlap
    return chunks

with open(output_file, "w", encoding="utf-8") as out:
    for directory in dirs:
        if not os.path.exists(directory):
            print(f"❌ Directory not found: {directory}")
            continue

        for filename in os.listdir(directory):
            if filename.endswith(".md"):
                path = os.path.join(directory, filename)
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read().strip()

                if len(content) < 100:
                    continue  # skip too-short files

                content = remove_image_tags(content)

                chunks = chunk_text(content, chunk_size, overlap)
                for i, chunk in enumerate(chunks):
                    record = {
                        "source": os.path.join(directory, filename),
                        "chunk_id": f"{filename}_part_{i+1}",
                        "text": chunk
                    }
                    out.write(json.dumps(record) + "\n")

print(f"✅ Done. Clean chunks saved to {output_file}")
