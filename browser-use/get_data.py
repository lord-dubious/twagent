import requests
import json
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os

# Get current time and subtract fifteen minutes
current_time = datetime.now()
fifteen_minutes_ago = current_time - timedelta(minutes=15)
start_date = fifteen_minutes_ago.strftime("%Y-%m-%dT%H:%M:%S.000Z")

SCRIPT_DIR = os.path.dirname(__file__)
pathToData = "../data"
users_file = "/004_users.json"

load_dotenv()
token = os.getenv("TOKEN")
url = "https://api.brightdata.com/datasets/v3/trigger"
headers = {
	"Authorization": "Bearer " + token,
	"Content-Type": "application/json",
}
params = {
	"dataset_id": "gd_lwxkxvnf1cynvib9co",
	"include_errors": "true",
	"type": "discover_new",
	"discover_by": "profile_url",
	"limit_per_input": "3",
}

# Load users from 004_users.json
try:
    with open(os.path.join(SCRIPT_DIR, pathToData + users_file), 'r') as users_file:
        users_data = json.load(users_file)
        
    # Filter users whose score is not 100
    filtered_users = [user for user in users_data if user.get('score') != 100]
    
    # Create data array with URLs from handles - limit to 3 users
    data = []
    for user in filtered_users[:3]:  # Only take the first 3 users
        handle = user['handle']
        # Remove @ symbol if present
        if handle.startswith('@'):
            handle = handle[1:]
        
        data.append({
            "url": f"https://x.com/{handle}",
            "start_date": start_date,
            "end_date": ""
        })
    
    print(f"Processing {len(data)} users")
    
except (FileNotFoundError, json.JSONDecodeError) as e:
    print(f"Error loading users file: {e}")
    # Fallback to default if there's an error
    data = [
        {"url":"https://x.com/DOGE","start_date": start_date,"end_date":""},
    ]

response = requests.post(url, headers=headers, params=params, json=data)
print(response.json())

snapshot_id = response.json().get('snapshot_id')
url = f"https://api.brightdata.com/datasets/v3/snapshot/{snapshot_id}"
headers = {
    "Authorization": "Bearer " + token
}
params = {"format": "json"}

while True:
    time.sleep(40)  # Wait for 40 seconds

    response = requests.request("GET", url, headers=headers)
    print(response.text)
    if response.text == "200":
        break;
    if response.text == "Snapshot is empty":
        break;
if response.text != "Snapshot is empty":
        
    response = requests.get(url, headers=headers, params=params)
    new_data = response.json()

    # Load existing data if file exists
    try:
        with open(os.path.join(SCRIPT_DIR, pathToData, '001_saved_tweets.json'), 'r') as json_file:
            existing_data = json.load(json_file)
    except (FileNotFoundError, json.JSONDecodeError):
        existing_data = []

    # Create a dictionary from existing data for easy lookup
    existing_dict = {item['id']: item for item in existing_data}

    # Merge new data, replacing duplicates
    for item in new_data:
        existing_dict[item['id']] = item

    # Convert back to list
    merged_data = list(existing_dict.values())

    # Save merged data
    with open(os.path.join(SCRIPT_DIR, pathToData, '001_saved_tweets.json'), 'w') as json_file:
        json.dump(merged_data, json_file, indent=2)