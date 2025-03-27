import requests
import json
import time
from datetime import datetime, timedelta

# Get current time and subtract one hour
current_time = datetime.now()
one_hour_ago = current_time - timedelta(hours=1)
start_date = one_hour_ago.strftime("%Y-%m-%dT%H:%M:%S.000Z")

url = "https://api.brightdata.com/datasets/v3/trigger"
headers = {
	"Authorization": "Bearer 377d1f523bde47c92a63dd9c4dac26ee11abc2874652cbb5e525a0ad58308307",
	"Content-Type": "application/json",
}
params = {
	"dataset_id": "gd_lwxkxvnf1cynvib9co",
	"include_errors": "true",
	"type": "discover_new",
	"discover_by": "profile_url",
	"limit_per_input": "7",
}

data = [
	{"url":"https://x.com/elonmusk","start_date": start_date,"end_date":""},
]

response = requests.post(url, headers=headers, params=params, json=data)
print(response.json())

snapshot_id = response.json().get('snapshot_id')
url = f"https://api.brightdata.com/datasets/v3/snapshot/{snapshot_id}"
headers = {
	"Authorization": "Bearer 377d1f523bde47c92a63dd9c4dac26ee11abc2874652cbb5e525a0ad58308307",
}
params = {"format": "json"}

for i in range(60, 0, -1):
    print(i)
    time.sleep(1)  # Wait for 1 second

response = requests.get(url, headers=headers, params=params)
new_data = response.json()

# Load existing data if file exists
try:
    with open('response_data.json', 'r') as json_file:
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
with open('response_data.json', 'w') as json_file:
    json.dump(merged_data, json_file, indent=2)