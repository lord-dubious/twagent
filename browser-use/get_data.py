import requests
import json
import time
import threading
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os
from concurrent.futures import ThreadPoolExecutor

# Get current time and subtract one hour
current_time = datetime.now()
# fifteen_minutes_ago = current_time - timedelta(minutes=15)
# one_hour_ago = current_time - timedelta(hours=1)
twelve_hours_ago = current_time - timedelta(hours=12)
start_date = twelve_hours_ago.strftime("%Y-%m-%dT%H:%M:%S.000Z")

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

# Function to process a batch of users
def process_user_batch(batch):
	# Create data array with URLs from handles
	data = []
	for user in batch:
		handle = user['handle']
		# Remove @ symbol if present
		if handle.startswith('@'):
			handle = handle[1:]
		
		data.append({
			"url": f"https://x.com/{handle}",
			"start_date": start_date,
			"end_date": ""
		})
	
	print(f"Processing batch of {len(data)} users")
	#print(f"API request data: {json.dumps(data, indent=2)}")
	
	try:
		#print(f"Making API request to: {url}")
		response = requests.post(url, headers=headers, params=params, json=data)
		print(f"API response status code: {response.status_code}")
		print(f"API response: {response.text[:1000]}...")  # Print first 1000 chars
		
		response_json = response.json()
		print(f"Parsed response JSON: {json.dumps(response_json, indent=2)}")
		
		snapshot_id = response_json.get('snapshot_id')
		if not snapshot_id:
			print(f"Error: No snapshot_id in response")
			return
			
		print(f"Got snapshot_id: {snapshot_id}")
		snapshot_url = f"https://api.brightdata.com/datasets/v3/snapshot/{snapshot_id}"
		snapshot_headers = {
			"Authorization": "Bearer " + token
		}
		snapshot_params = {"format": "json"}
		
		print(f"Will check snapshot status at: {snapshot_url}")
		
		attempts = 0
		max_attempts = 5
		while attempts < max_attempts:
			attempts += 1
			print(f"Waiting 40 seconds before checking snapshot status (attempt {attempts}/{max_attempts})...")
			time.sleep(40)  # Wait for 40 seconds
			
			print(f"Checking snapshot status...")
			status_response = requests.request("GET", snapshot_url, headers=snapshot_headers)
			print(f"Status response code: {status_response.status_code}")
			print(f"Batch status: {status_response.text}")
			
			if status_response.text == "200" or status_response.text == "Snapshot is empty":
				print(f"Snapshot is ready or empty")
				break
			
			if attempts == max_attempts:
				print(f"Reached maximum attempts. Last status: {status_response.text}")
		
		if status_response.text != "Snapshot is empty":
			print(f"Snapshot is not empty, retrieving data...")
			data_response = requests.get(snapshot_url, headers=snapshot_headers, params=snapshot_params)
			print(f"Data response status code: {data_response.status_code}")
			print(f"Data response content type: {data_response.headers.get('Content-Type', 'unknown')}")
			print(f"Data response length: {len(data_response.text)} bytes")
			print(f"Data response preview: {data_response.text[:500]}...")  # Print first 500 chars
			
			# The API might return a string with multiple JSON objects, each on a new line
			# We need to parse this properly
			response_text = data_response.text.strip()
			new_data = []
			
			if response_text:
				print(f"Parsing response text...")
				# Check if the response is a JSON array or multiple JSON objects
				if response_text.startswith('[') and response_text.endswith(']'):
					# It's a JSON array
					print(f"Response appears to be a JSON array")
					new_data = json.loads(response_text)
				else:
					# It's multiple JSON objects, each on a new line
					print(f"Response appears to be multiple JSON objects, parsing line by line")
					for line_num, line in enumerate(response_text.split('\n')):
						if line.strip():
							try:
								tweet_data = json.loads(line.strip())
								new_data.append(tweet_data)
								if line_num < 2:  # Print details of first two items for debugging
									print(f"Successfully parsed item {line_num+1}: {json.dumps(tweet_data)[:200]}...")
							except json.JSONDecodeError as e:
								print(f"Error parsing line {line_num+1}: {e}")
								print(f"Problematic line: {line[:100]}...")
			
			print(f"Received {len(new_data)} items from API")
			
			if not new_data:
				print("Warning: No valid data received from API")
				return
				
			# Lock to prevent race conditions when writing to the file
			with file_lock:
				print(f"Acquired file lock, updating 001_saved_tweets.json")
				# Load existing data if file exists
				file_path = os.path.join(SCRIPT_DIR, pathToData, '001_saved_tweets.json')
				print(f"File path: {file_path}")
				
				existing_data = []
				try:
					if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
						print(f"Existing file has content, parsing JSON")
						with open(file_path, 'r') as json_file:
							file_content = json_file.read().strip()
							if file_content:
								existing_data = json.loads(file_content)
								print(f"Loaded {len(existing_data)} existing items")
							else:
								print(f"Existing file is empty, starting with empty list")
					else:
						print(f"File doesn't exist or is empty, creating new file")
				except (FileNotFoundError, json.JSONDecodeError) as e:
					print(f"Error reading existing file: {e}. Starting with empty list.")
				
				# Create a dictionary from existing data for easy lookup
				print(f"Creating lookup dictionary from existing data")
				existing_dict = {item.get('id', f'item_{i}'): item for i, item in enumerate(existing_data)}
				
				# Merge new data, replacing duplicates
				print(f"Merging {len(new_data)} new items into existing data")
				for item in new_data:
					item_id = item.get('id', f'new_item_{len(existing_dict)}')
					existing_dict[item_id] = item
				
				# Convert back to list
				merged_data = list(existing_dict.values())
				
				# Save merged data
				print(f"Saving {len(merged_data)} total items to file")
				try:
					with open(file_path, 'w') as json_file:
						json.dump(merged_data, json_file, indent=2)
					print(f"Successfully saved data to {file_path}")
				except Exception as e:
					print(f"Error saving data to file: {e}")
				
				print(f"Saved {len(new_data)} new items from batch. Total items: {len(merged_data)}")
	except Exception as e:
		print(f"Error processing batch: {e}")
		import traceback
		traceback.print_exc()

# Create a lock for file operations
file_lock = threading.Lock()

# Load users from 004_users.json
try:
	with open(os.path.join(SCRIPT_DIR, pathToData + users_file), 'r') as f:
		users_data = json.load(f)
		
	# Filter users whose score is not 100
	filtered_users = [user for user in users_data if user.get('score') != 100]
	
	# Split users into batches of 3
	batches = [filtered_users[i:i+3] for i in range(0, len(filtered_users), 3)]
	print(f"Processing {len(filtered_users)} users in {len(batches)} batches")

	# Just take the first three users
	#first_three_users = filtered_users[:3]
	#batches = [first_three_users]

	# Print the handles of all users who will be processed
	print("Users who will be processed:")
	for batch_index, batch in enumerate(batches):
		print(f"Batch {batch_index + 1}:")
		for user_index, user in enumerate(batch):
			print(f"  {user_index + 1}. {user['handle']}")
	
	# Process batches in parallel using ThreadPoolExecutor
	with ThreadPoolExecutor(max_workers=5) as executor:  # Limit to 5 concurrent threads
		executor.map(process_user_batch, batches)
	
except (FileNotFoundError, json.JSONDecodeError) as e:
	print(f"Error loading users file: {e}")