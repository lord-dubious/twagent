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

load_dotenv()

SCRIPT_DIR = os.path.dirname(__file__)

pathToData = "../data"
users = "/004_users.json"

    
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


    def kickoff(self):
        """Start the workflow"""
        self.follow_accounts()
        self.block_accounts()

    
    def follow_accounts(self):
        try:
            with open(os.path.join(SCRIPT_DIR, pathToData + users), "r") as f:
                data = json.load(f)
                if data:
                    filtered_data = {user['handle']: user['score'] for user in data if user['score'] != 100 and not user.get('alreadyFollowingOrBlocked', False)}
                    print(filtered_data)

                    from my_twitter_api_v3.follows.follow_user import follow_user
                    import asyncio
                    for user_handle in filtered_data.keys():
                        asyncio.run(follow_user(handle=user_handle))
                        # Update the 'alreadyFollowingOrBlocked' field to True for each followed user
                        for user in data:
                            if user['handle'] in filtered_data:
                                user['alreadyFollowingOrBlocked'] = True

                        # Save the updated data back to the file
                        with open(os.path.join(SCRIPT_DIR, pathToData + users), "w") as f:
                            json.dump(data, f, indent=2)
                    return True
            return False


        except FileNotFoundError:
            print("The generated_tweets.json file does not exist.")
            return False
        except json.JSONDecodeError:
            print("Error decoding the generated_tweets.json file.")
            return False
    def block_accounts(self):
        try:
            with open(os.path.join(SCRIPT_DIR, pathToData + users), "r") as f:
                data = json.load(f)
                if data:
                    filtered_data = {user['handle']: user['score'] for user in data if user['score'] == 100 and not user.get('alreadyFollowingOrBlocked', False)}
                    print(filtered_data)

                    from my_twitter_api_v3.follows.follow_user import follow_user
                    import asyncio
                    for user_handle in filtered_data.keys():
                        asyncio.run(follow_user(handle=user_handle))
                        # Update the 'alreadyFollowingOrBlocked' field to True for each followed user
                        for user in data:
                            if user['handle'] in filtered_data:
                                user['alreadyFollowingOrBlocked'] = True

                        # Save the updated data back to the file
                        with open(os.path.join(SCRIPT_DIR, pathToData + users), "w") as f:
                            json.dump(data, f, indent=2)
                    return True
            return False


        except FileNotFoundError:
            print("The generated_tweets.json file does not exist.")
            return False
        except json.JSONDecodeError:
            print("Error decoding the generated_tweets.json file.")
            return False


if __name__ == "__main__":
    workflow = TweetCreatorFlow()
    workflow.kickoff()