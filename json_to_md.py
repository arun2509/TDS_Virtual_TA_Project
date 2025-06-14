import os
import json
from datetime import datetime

os.makedirs("topics_md", exist_ok=True)

for file in os.listdir("topics_json"):
    with open(f"topics_json/{file}", "r") as f:
        data = json.load(f)

    title = data.get("title", "Untitled Topic")
    posts = data.get("post_stream", {}).get("posts", [])

    md_lines = [f"# {title}\n"]

    for post in posts:
        author = post.get("username", "Unknown")
        created = post.get("created_at", "")
        content = post.get("cooked", "")

        md_lines.append(f"---\n**{author}** *(created: {created})*\n\n{content}\n")

    # Save to .md
    topic_id = data.get("id", "unknown")
    with open(f"topics_md/{topic_id}.md", "w", encoding="utf-8") as out:
        out.write("\n".join(md_lines))
