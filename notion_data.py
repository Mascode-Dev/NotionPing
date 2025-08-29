import os
import requests
import notion_data
from dotenv import load_dotenv
from database_models import DatabaseManager
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

def event_in_db():
    data_events = get_notion_events()["results"]
    db_manager = DatabaseManager()
    all_events = db_manager.get_all_events()

    for event in all_events:
        if event.notion_id in [e['id'] for e in data_events]:
            print(f"✓ Événement déjà présent dans la base de données: {event.title}")
            # Supprimer l'event de data_event
            data_events = [e for e in data_events if e['id'] != event.notion_id]
        else:
            print(f"✗ Nouvel événement à ajouter à la base de données: {event.title}")

    for event in data_events:
        notion_id = event['id']
        created_by = event['created_by']['id']
        created_at = event['created_time']

        archived = event['archived']
        title = event['properties']['Name']['title'][0]['text']['content']
        description = event['properties']['Description']['rich_text'][0]['text']['content']
        price = event['properties']['Prix']['number']
        date = event['properties']['Date']['date']['start']

        participant = []
        for person in event['properties']['Participants']['people']:
            participant.append(person['id'])
            
        status = event['properties']['Type']['status']['name']
        updated_at = event['last_edited_time']

        duration = event['properties']['Durée']['rich_text'][0]['text']['content'] if event['properties']['Durée']['rich_text'] else None
        location = event['properties']['Lieu']['rich_text'][0]['text']['content'] if event['properties']['Lieu']['rich_text'] else None
        limit_date = event['properties']['Date limite choix de participation']['date']['start'] if event['properties']['Date limite choix de participation']['date'] else None
        # Add to db
        db_manager = DatabaseManager()
        db_manager.add_event(
            notion_id=notion_id,
            
            title=title,
            description=description,
            price=price,
            date=date,
            created_by=created_by,
            archived=archived,
            participant=participant,
            updated_at=updated_at,
            created_at=created_at,
            status=status,
            duration=duration,
            location=location,
            limit_date=limit_date
        )
    return data_events

if __name__ == "__main__":
    event_in_db()