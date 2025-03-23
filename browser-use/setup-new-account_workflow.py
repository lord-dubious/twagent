#!/usr/bin/env python
import json
import os
import math
from typing import List
from pydantic import BaseModel, Field
import random
import datetime  # Add this import at the top with other imports
from openai import OpenAI
from dotenv import load_dotenv  # Add this import
import asyncio
import string  # Add this import

load_dotenv()

SCRIPT_DIR = os.path.dirname(__file__)

pathToData = "../data"
aboutMe = "/000_about_me.json"
users = "/004_users.json"
lists = "/005_lists.json"

    
# Simple LLM mock class for generating responses
class LLM:
    def __init__(self, model, response_format=None):
        self.model = model
        self.response_format = response_format
        
    def call(self, messages):
        # Real implementation that calls OpenAI API
        
        try:
            # Get API key from environment variable
            api_key = os.environ.get("OPENAI_API_KEY")
                
            client = OpenAI(api_key=api_key)
            
            completion = client.chat.completions.create(
                model="gpt-4o-mini-2024-07-18",
                messages=messages,  # Use the messages passed to the function
                response_format={"type": "json_object"}  # Request JSON response format
            )
            print(completion.choices[0].message.content)
            # Extract the content from the response
            return completion.choices[0].message.content
            
        except Exception as e:
            print(f"Error calling OpenAI API: {str(e)}")
            
            # Fallback to mock response if API call fails
            options = []
            for i in range(10):
                options.append({
                    "tweet_text": f"hmm {i+1}."
                })
            return json.dumps({"tweet_options": options})

class TweetCreatorFlow:
    def get_about(self):
        with open(os.path.join(SCRIPT_DIR, pathToData + aboutMe), "r") as f:
            data = json.load(f)
            self.handle = data[0]['handle'] if data else None
        return self
    
    async def kickoff(self):
        """Start the workflow"""
        self.get_about()
        await self.follow_accounts()
        await self.block_accounts()
        #await self.create_list()
        await self.add_members_to_list()
        return True

    async def follow_accounts(self):
        try:
            with open(os.path.join(SCRIPT_DIR, pathToData + users), "r") as f:
                data = json.load(f)
                if data:
                    filtered_data = {user['handle']: user['score'] for user in data if user['score'] != 100 and not user.get('alreadyFollowingOrBlocked', False)}
                    print(filtered_data)

                    from my_twitter_api_v3.follows.follow_user import follow_user
                    for user_handle in filtered_data.keys():
                        await follow_user(handle=user_handle)
                        # Update the 'alreadyFollowingOrBlocked' field
                        for user in data:
                            if user['handle'] in filtered_data:
                                user['alreadyFollowingOrBlocked'] = True

                        # Save the updated data
                        with open(os.path.join(SCRIPT_DIR, pathToData + users), "w") as f:
                            json.dump(data, f, indent=2)
                    return True
            return False


        except FileNotFoundError:
            print("The 004_users.json file does not exist.")
            return False
        except json.JSONDecodeError:
            print("Error decoding the 004_users.json file.")
            return False
        
    async def block_accounts(self):
        try:
            with open(os.path.join(SCRIPT_DIR, pathToData + users), "r") as f:
                data = json.load(f)
                if data:
                    filtered_data = {user['handle']: user['score'] for user in data if user['score'] == 100 and not user.get('alreadyFollowingOrBlocked', False)}
                    print(filtered_data)

                    from my_twitter_api_v3.blocks.block_user import block_user
                    for user_handle in filtered_data.keys():
                        await block_user(handle=user_handle)
                        
                        # Update the 'alreadyFollowingOrBlocked' field
                        for user in data:
                            if user['handle'] in filtered_data:
                                user['alreadyFollowingOrBlocked'] = True

                        # Save the updated data
                        with open(os.path.join(SCRIPT_DIR, pathToData + users), "w") as f:
                            json.dump(data, f, indent=2)
                    return True
            return False
        except FileNotFoundError:
            print("The 004_users.json file does not exist.")
            return False
        except json.JSONDecodeError:
            print("Error decoding the 004_users.json file.")
            return False

        
    async def create_list(self):
        def generate_random_name(length=8):
            letters = string.ascii_lowercase
            return ''.join(random.choice(letters) for i in range(length))

        name = generate_random_name()
        from my_twitter_api_v3.lists.create_list import create_list
        await create_list(name=name)
        with open(os.path.join(SCRIPT_DIR, pathToData + lists), "w") as f:
            json.dump({"name": name, "handles": []}, f, indent=2)
        return True
    
    async def add_members_to_list(self):
        try:
            with open(os.path.join(SCRIPT_DIR, pathToData + users), "r") as f:
                data = json.load(f)
                if data:
                    filtered_data = {user['handle']: user['score'] for user in data if user['score'] == 100 and not user.get('alreadyFollowingOrBlocked', False)}
                    print(filtered_data)

                    from my_twitter_api_v3.lists.add_members_to_list import add_members_to_list
                    for user_handle in filtered_data.keys():
                        await block_user(handle=user_handle)
                        
                        # Update the 'alreadyFollowingOrBlocked' field
                        for user in data:
                            if user['handle'] in filtered_data:
                                user['alreadyFollowingOrBlocked'] = True

                        # Save the updated data
                        with open(os.path.join(SCRIPT_DIR, pathToData + users), "w") as f:
                            json.dump(data, f, indent=2)
                    return True
            return False
        except FileNotFoundError:
            print("The 004_users.json file does not exist.")
            return False
        except json.JSONDecodeError:
            print("Error decoding the 004_users.json file.")
            return False

if __name__ == "__main__":
    workflow = TweetCreatorFlow()
    asyncio.run(workflow.kickoff())