# convert_topics_json_to_markdown.py

import json
from pathlib import Path
import html2text

def convert_topics_json(json_dir: str, md_dir: str):
    json_path = Path(json_dir)
    output_path = Path(md_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    converter = html2text.HTML2Text()
    converter.ignore_images = True
    converter.ignore_links = False
    converter.body_width = 0  # avoid line wrapping

    count = 0
    for json_file in json_path.glob("*.json"):
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        posts = data.get("post_stream", {}).get("posts", [])
        if not posts:
            continue

        topic_id = data.get("id") or json_file.stem
        title = data.get("title") or f"Topic {topic_id}"

        lines = [f"# {title} (ID: {topic_id})", ""]
        for post in posts:
            author = post.get("name") or post.get("username", "Unknown")
            created = post.get("created_at", "")
            html = post.get("cooked", "")
            md = converter.handle(html).strip()

            lines.append(f"**{author}** (_{created}_)")
            lines.append("")
            lines.append(md)
            lines.append("\n---\n")

        md_file = output_path / f"topic_{topic_id}.md"
        md_file.write_text("\n".join(lines), encoding="utf-8")
        count += 1

    print(f"✅ Converted {count} JSON files into Markdown in '{md_dir}'")

if __name__ == "__main__":
    convert_topics_json("topics_json", "topics_md")
