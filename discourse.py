import requests
import json

# Step 1: Read cookie string from file
with open("cookies.txt", "r") as file:
    cookie = file.read().strip()

# Step 2: Prepare headers with cookie
headers = {
    "cookie": cookie,
    "User-Agent": "Mozilla/5.0"
}

# Step 3: Send GET request to Discourse API
url = "https://discourse.onlinedegree.iitm.ac.in/tags/c/courses/tds-kb/34/term1-2025/l/latest.json?match_all_tags=true&page=1&tags%5B%5D=term1-2025"
response = requests.get(url, headers=headers)

# Step 4: Write response JSON to file
with open("discourse.json", "w") as file:
    json.dump(response.json(), file, indent=4)

print("✅ JSON saved to discourse.json")
