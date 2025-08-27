import os
import requests
import notion_data
from dotenv import load_dotenv
import json

load_dotenv(dotenv_path=".env")

# Configuration

NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")
print("NOTION_API_KEY =", os.getenv("NOTION_API_KEY"))
print("NOTION_DATABASE_ID =", os.getenv("NOTION_DATABASE_ID"))

headers = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"  # Use the latest API version
}

def verify_database(db_id):
    url = f"https://api.notion.com/v1/databases/{db_id}"
    res = requests.get(url, headers=headers)
    if res.status_code == 200:
        print("✅ Valid database ID!")
        return res.json()
    else:
        print(f"❌ Error: {res.text}")
        return None

def get_notion_events():
    data = {
        "filter": {
            "property": "Date",
            "date": {
            "on_or_after": "2025-01-01"
            }
        },
        "sorts": [
            {
            "property": "Date",
            "direction": "ascending"
            }
        ]
    }
    url = f"https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}/query"
    res = requests.post(url, headers=headers, json=data)
    res.raise_for_status()
    data = res.json()
    
    # Dump the result in a json file
    with open("notion_events.json", "w") as f:
        json.dump(data, f, indent=4)
    return data



print(get_notion_events())
