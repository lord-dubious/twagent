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
load_dotenv()

browser = Browser()
initial_actions = [
	{'open_tab': {'url': 'https://www.x.com/DOGE'}},
]

file_path = os.path.join(os.path.dirname(__file__), 'twitter_cookies.txt')
context = BrowserContext(browser=browser, config=BrowserContextConfig(cookies_file=file_path))

class Tweet(BaseModel):
    author: str
    handle: str
    datetime: str
    content: str

class Tweets(BaseModel):
    tweets: list[Tweet]

controller = Controller(output_model=Tweets)

async def main():

    agent = Agent(
        task="Find the latest tweet on DOGE's (Department of Government Efficiency) twitter profile.",
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
        json_file_path = "saved_tweets.json"
        existing_tweets = []
        if os.path.exists(json_file_path):
            try:
                with open(json_file_path, "r") as f:
                    existing_data = json.load(f)
                    existing_tweets = existing_data.get("tweets", [])
            except json.JSONDecodeError:
                print("Error reading existing tweets file. Starting with empty list.")
        
        # Check each tweet and add if not already in the file
        new_tweets_added = False
        for tweet in parsed.tweets:
            # Create a dictionary representation of the tweet
            tweet_dict = {
                "author": tweet.author,
                "handle": tweet.handle,
                "datetime": tweet.datetime,
                "content": tweet.content
            }
            
            # Check if this tweet is already in our existing tweets
            if not any(
                existing["handle"] == tweet.handle and 
                existing["datetime"] == tweet.datetime and
                existing["content"] == tweet.content
                for existing in existing_tweets
            ):
                existing_tweets.append(tweet_dict)
                new_tweets_added = True
                print(f"Added new tweet from {tweet.handle}")
            
            # Print tweet info
            print(f"Author: {tweet.author}")
            print(f"Handle: {tweet.handle}")
            print(f"Datetime: {tweet.datetime}")
            print(f"Content: {tweet.content}")
            print()
        
        # Save updated tweets list if any new tweets were added
        if new_tweets_added:
            with open(json_file_path, "w") as f:
                json.dump({"tweets": existing_tweets}, f, indent=2)
                print(f"Updated tweets saved to {json_file_path}")
    else:
        print('No result')


asyncio.run(main())