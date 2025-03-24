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
import argparse  # Added for command line arguments

load_dotenv()

class Tweet(BaseModel):
    handle: str | None
    display_name: str | None
    text: str | None
    likes: int | None
    retweets: int | None
    replies: int | None
    bookmarks: int | None
    tweet_link: str | None
    viewcount: int | None
    datetime: str | None

SCRIPT_DIR = os.path.dirname(__file__)

pathToData = "../../../data"
aboutMe = "/000_about_me.json"
lastSavedTweets = "/001_saved_tweets.json"


async def get_tweet(post_url="https://twitter.com/TheBabylonBee/status/1903616058562576739"):

    initial_actions = [
        {'open_tab': {'url': post_url}},  # Use the provided tweet URL
    ]

    file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'twitter_cookies.txt')
    # Use script location as reference point for json file path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    json_file_path = os.path.join(script_dir, "../../../data/saved_tweets.json")
    # Make the path absolute to resolve the relative components
    json_file_path = os.path.abspath(json_file_path)

    browser = Browser()
    controller = Controller(output_model=Tweet)
    context = BrowserContext(browser=browser, config=BrowserContextConfig(cookies_file=file_path))

    agent = Agent(
        task=(
            "Extract the tweet's: text, likes total, retweet total, reply total, bookmark total, tweet_link, the author's handle, the datetime it was psoted, and its viewcount"
        ),
        llm=ChatOpenAI(model="gpt-4o"),
        save_conversation_path="logs/conversation",  # Save chat logs
		browser_context=context,
        initial_actions=initial_actions,
        max_actions_per_step=6,
        controller=controller
    )
    history = await agent.run(max_steps=6)
    result = history.final_result()
    if result:
        parsed: Tweet = Tweet.model_validate_json(result)
        print(parsed)
        try:

            # Load existing tweets from JSON file if it exists
            existing_tweets = []
            with open(os.path.join(SCRIPT_DIR, pathToData + lastSavedTweets), "r") as f:
                data = json.load(f)
                existing_tweets = data.get("tweets", [])
        except FileNotFoundError:
            print("No existing tweets found. Starting with empty list.")
            existing_tweets = []
        except json.JSONDecodeError:
            print("Error reading existing tweets file. Starting with empty list.")
            existing_tweets = []

        # Create a dictionary representation of the tweet
        tweet_dict = {
            "handle": parsed.handle,
            "datetime": parsed.datetime,
            "text": parsed.text,
            "likes": parsed.likes,
            "retweets": parsed.retweets,
            "replies": parsed.replies,
            "bookmarks": parsed.bookmarks,
            "tweet_url": post_url,
            "viewcount": parsed.viewcount
        }

        # Check if the tweet's URL matches the post_url and update or add it
        updated = False
        print(existing_tweets)
        for i, existing in enumerate(existing_tweets):
            if existing["tweet_url"] == tweet_dict["tweet_url"]:
                existing_tweets[i] = tweet_dict
                updated = True
                print(f"Updated tweet from {tweet_dict['handle']} at {post_url}")
                break
        
        if not updated:
            existing_tweets.append(tweet_dict)
            print(f"Added new tweet from {tweet_dict['handle']} at {post_url}")

        # Save updated tweets list
        with open(os.path.join(SCRIPT_DIR, pathToData + lastSavedTweets), "w") as f:
            json.dump({"tweets": existing_tweets}, f, indent=2)
            print(f"Updated tweets saved.")
    else:
        print('No result')
    return True

if __name__ == "__main__":
    get_tweet()