import requests
import json


with open("cookies.txt", "r") as file:
    cookie = file.read().strip()

headers = {
    "cookie": cookie
}
response = requests.get("https://discourse.onlinedegree.iitm.ac.in/t/166576/posts.json?post_ids%5B%5D=602915&post_ids%5B%5D=603351&post_ids%5B%5D=605775&include_suggested=false", headers=headers)

with open("discourse11.json", "w") as file:
    json.dump(response.json(), file, indent=4)