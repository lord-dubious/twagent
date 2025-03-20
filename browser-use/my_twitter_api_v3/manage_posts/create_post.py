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
	{'open_tab': {'url': 'https://pro.x.com/i/decks/1902192120082866405'}},
]

file_path = os.path.join(os.path.dirname(__file__), 'twitter_cookies.txt')
context = BrowserContext(browser=browser, config=BrowserContextConfig(cookies_file=file_path))
json_file_path = "posted_tweets.json"


controller = Controller()

async def main():

    my_post = "Chicago's sunset is beautiful right now."
    agent = Agent(
        task=(
            "Post a tweet saying:" + my_post
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

        with open(json_file_path, "w") as f:
            json.dump({"tweets": my_post}, f, indent=2)
            print(f"Updated tweets saved to {json_file_path}")
    else:
        print('No result')


asyncio.run(main())