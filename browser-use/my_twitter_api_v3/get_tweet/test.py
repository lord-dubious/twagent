from langchain_openai import ChatOpenAI
from browser_use import Agent, Browser
from pydantic import SecretStr
from pydantic import BaseModel

from browser_use import Agent, ActionResult, Controller
from browser_use.browser.browser import Browser, BrowserConfig
from browser_use.browser.context import BrowserContext, BrowserContextConfig

import os
import asyncio
from dotenv import load_dotenv
import json
import os.path
from datetime import datetime

load_dotenv()

browser = Browser()
initial_actions = [
	{'open_tab': {'url': 'https://x.com/ShawnOnTheRight/status/1902883820468044200'}},
]

file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'twitter_cookies.txt')
# Use script location as reference point for json file path
script_dir = os.path.dirname(os.path.abspath(__file__))
json_file_path = os.path.join(script_dir, "../../../data/saved_tweets.json")
# Make the path absolute to resolve the relative components
json_file_path = os.path.abspath(json_file_path)

class Tweet(BaseModel):
    handle: str
    display_name: str
    text: str
    likes: int
    retweets: int
    replies: int
    bookmarks: int
    tweet_link: str
    viewcount: int
    datetime: str

class Tweets(BaseModel):
    tweets: list[Tweet]

controller = Controller(output_model=Tweets)
context = BrowserContext(browser=browser, config=BrowserContextConfig(cookies_file=file_path))

async def main():

    agent = Agent(
        task=(
            "Return the tweet's text, datetime, viewcount, comments, reposts, "
            "likes, bookmarks"
        ),
        llm=ChatOpenAI(model="gpt-4o"),
        save_conversation_path="logs/conversation",  # Save chat logs
		browser_context=context,
        initial_actions=initial_actions,
        max_actions_per_step=4,
        controller=controller
    )
    history = await agent.run(max_steps=10)
    result = history.final_result()
    if result:
        parsed: Tweets = Tweets.model_validate_json(result)
        
        # Load existing tweets from JSON file if it exists
        existing_tweets = []
        if os.path.exists(json_file_path):
            try:
                with open(json_file_path, "r") as f:
                    existing_data = json.load(f)
                    existing_tweets = existing_data.get("tweets", [])
            except json.JSONDecodeError:
                print("Error reading existing tweets file. Starting with empty list.")
        
        # Check each tweet and add if not already in the file¬
        new_tweets_added = False
        for tweet in parsed.tweets:
            # Create a dictionary representation of the tweet
            tweet_dict = {
                "handle": tweet.handle,
                "datetime": tweet.datetime,
                "text": tweet.text,
                "likes": tweet.likes,
                "retweets": tweet.retweets,
                "replies": tweet.replies,
                "bookmarks": tweet.bookmarks,
                "tweet_link": tweet.tweet_link,
                "viewcount": tweet.viewcount
            }
            
            # Check if this tweet is already in our existing tweets
            if not any(
                existing["handle"] == tweet.handle and 
                existing["datetime"] == tweet.datetime and
                existing["text"] == tweet.text
                for existing in existing_tweets
            ):
                existing_tweets.append(tweet_dict)
                new_tweets_added = True
                print(f"Added new tweet from {tweet.handle}")
            
        
        # Save updated tweets list if any new tweets were added
        if new_tweets_added:
            with open(json_file_path, "w") as f:
                json.dump({"tweets": existing_tweets}, f, indent=2)
                print(f"Updated tweets saved to {json_file_path}")
    else:
        print('No result')


asyncio.run(main())