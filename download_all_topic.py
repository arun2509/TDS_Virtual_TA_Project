import os
import json
import requests

# Step 1: Read cookie string from file
with open("cookies.txt", "r") as file:
    cookie = file.read().strip()

# Step 2: Prepare headers
headers = {
    "cookie": cookie,
    "User-Agent": "Mozilla/5.0"
}

# Step 3: Load topic list JSON (output from your earlier stage)
with open("discourse.json", "r") as f:
    topic_data = json.load(f)

topics = topic_data["topic_list"]["topics"]

# Step 4: Create a directory to store all topic JSONs
os.makedirs("topics_json", exist_ok=True)

# Step 5: Loop and fetch each topic
base_url = "https://discourse.onlinedegree.iitm.ac.in"

for topic in topics:
    topic_id = topic["id"]
    slug = topic["slug"]
    url = f"{base_url}/t/{slug}/{topic_id}.json?track_visit=true&forceLoad=true"

    print(f"📥 Fetching topic: {topic_id} - {slug}")
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        with open(f"topics_json/{topic_id}.json", "w") as out:
            json.dump(response.json(), out, indent=4)
        print(f"✅ Saved: {topic_id}.json")
    else:
        print(f"❌ Failed: {topic_id} (Status: {response.status_code})")
