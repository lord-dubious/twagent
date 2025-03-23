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
	{'open_tab': {'url': 'https://pro.x.com'}},
]

file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'twitter_cookies.txt')
# Use script location as reference point for json file path
script_dir = os.path.dirname(os.path.abspath(__file__))
json_file_path = os.path.join(script_dir, "../../../data/decks.json")
# Make the path absolute to resolve the relative components
json_file_path = os.path.abspath(json_file_path)


controller = Controller()

async def main():

    deck_name = "koala"
    column_type = "explore"
    agent = Agent(
        task=(
            "Create a new deck. Name it " + deck_name + 
            ". Add column. Set to " + column_type + "."
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
            json.dump({"deck_name": deck_name, "column_type": column_type}, f, indent=2)
            print(f"Updated decks saved to {json_file_path}")
    else:
        print('No result')


asyncio.run(main())