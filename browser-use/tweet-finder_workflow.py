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
load_dotenv()

SCRIPT_DIR = os.path.dirname(__file__)

pathToData = "../data"
aboutMe = "/000_about_me.json"
lastSavedTweets = "/001_saved_tweets.json"

    
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
    

    def kickoff(self):
        self.get_about()
        #self.monitor_list_updates()
        self.get_tweet_here()
        return True

    def monitor_list_updates(self):
        from my_twitter_api_v3.lists.get_list_posts_timeline import get_list_posts
        new_tweets = get_list_posts()
        print(new_tweets)
        
        # Read existing data first
        try:
            with open(os.path.join(SCRIPT_DIR, pathToData + lastSavedTweets), "r") as f:
                existing_data = json.load(f)
                # Ensure proper structure
                if "tweets" not in existing_data or not isinstance(existing_data["tweets"], list):
                    existing_data = {"tweets": []}
                # Remove string entries if any exist
                existing_data["tweets"] = [t for t in existing_data["tweets"] if isinstance(t, dict)]
        except (FileNotFoundError, json.JSONDecodeError):
            # If file doesn't exist or is empty/invalid, start with empty structure
            existing_data = {"tweets": []}
        
        # Get existing tweet URLs to avoid duplicates
        existing_urls = {tweet.get("tweet_url", "") for tweet in existing_data["tweets"] 
                         if isinstance(tweet, dict) and "tweet_url" in tweet}
        
        # Only add new tweets that aren't already in the list
        for tweet in new_tweets:
            if isinstance(tweet, dict) and "tweet_url" in tweet and tweet["tweet_url"] not in existing_urls:
                existing_data["tweets"].append(tweet)
                existing_urls.add(tweet["tweet_url"])
        
        # Write the updated data back to the file
        with open(os.path.join(SCRIPT_DIR, pathToData + lastSavedTweets), "w") as f:
            json.dump(existing_data, f, indent=2)
        return True
    
    def get_tweet_here(self):

        # Load existing tweets from the JSON file
        with open(os.path.join(SCRIPT_DIR, pathToData + lastSavedTweets), "r") as f:
            existing_data = json.load(f)
            tweets = existing_data.get("tweets", [])
            
            # Iterate through each tweet
            for tweet in tweets:
                # Check if the tweet has a non-empty tweet_url and other fields are empty
                if tweet.get("tweet_url") and all(not tweet.get(key) for key in ["handle", "datetime", "text", "likes", "retweets", "replies", "bookmarks", "viewcount"]):
                    # Send the tweet_url to get_tweet
                    from my_twitter_api_v3.get_tweet.get_tweet import get_tweet
                    asyncio.run(get_tweet(tweet["tweet_url"]))
        return True
    

if __name__ == "__main__":
    workflow = TweetCreatorFlow()
    workflow.kickoff()