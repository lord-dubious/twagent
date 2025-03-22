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

initialTweet = "https://x.com/SolJakey/status/1903232593254027508"
browser = Browser()
initial_actions = [
	{'open_tab': {'url': initialTweet}},
    {'scroll_down': {'amount': 500}},

]

file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'twitter_cookies.txt')
# Use script location as reference point for json file path
script_dir = os.path.dirname(os.path.abspath(__file__))
json_file_path = os.path.join(script_dir, "../../../data/posted_tweets.json")
# Make the path absolute to resolve the relative components
json_file_path = os.path.abspath(json_file_path)


controller = Controller()
context = BrowserContext(browser=browser, config=BrowserContextConfig(cookies_file=file_path))

async def main():

    my_post = "gross"
    agent = Agent(
        task=(
            "Reply to the tweet with: " + my_post + " and then make sure to click the reply button."
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
        # Get current timestamp
        reply_time = datetime.now().isoformat()
        
        # Prepare data to save
        tweet_data = {
            "initial_tweet_url": initialTweet,
            "reply_text": my_post,
            "reply_time": reply_time
        }
        
        # Load existing data if file exists
        existing_data = []
        if os.path.exists(json_file_path) and os.path.getsize(json_file_path) > 0:
            try:
                with open(json_file_path, "r") as f:
                    existing_data = json.load(f)
                    # Convert to list if it's a single object
                    if not isinstance(existing_data, list):
                        existing_data = [existing_data]
            except json.JSONDecodeError:
                print("Error reading existing file. Starting with empty list.")
        
        # Append new data
        existing_data.append(tweet_data)
        
        # Save updated data
        with open(json_file_path, "w") as f:
            json.dump(existing_data, f, indent=2)
            print(f"Updated tweet data saved to {json_file_path}")
    else:
        print('No result')


asyncio.run(main())