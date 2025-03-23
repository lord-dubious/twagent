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


async def main(tweet_url = 'https://pro.x.com/i/decks/1902192120082866405',
    my_post = "I want mexican food right now."):




    browser = Browser()
    initial_actions = [
        {'open_tab': {'url': tweet_url}},
    ]

    file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'twitter_cookies.txt')
    # Use script location as reference point for json file path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    json_file_path = os.path.join(script_dir, "../../../data/posted_tweets.json")
    # Make the path absolute to resolve the relative components
    json_file_path = os.path.abspath(json_file_path)


    controller = Controller()
    context = BrowserContext(browser=browser, config=BrowserContextConfig(cookies_file=file_path))

    agent = Agent(
        task=(
            "Post a tweet saying:" + my_post
        ),
        llm=ChatOpenAI(model="gpt-4o-mini"),
        save_conversation_path="logs/conversation",  # Save chat logs
		browser_context=context,
        initial_actions=initial_actions,
        max_actions_per_step=4,
        controller=controller
    )
    history = await agent.run(max_steps=10)
    result = history.final_result()
    if result:
        reply_time = datetime.now().isoformat()

        # Prepare data to save
        tweet_data = {
            "reply_text": my_post,
            "reply_time": reply_time
        }
        
        with open(json_file_path, "w") as f:
            json.dump(tweet_data, f, indent=2)
            print(f"Updated tweet data saved to {json_file_path}")
    else:
        print('No result')

if __name__ == "__main__":
    asyncio.run(main())