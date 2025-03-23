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


async def follow_user(handle = "@doge"):

    browser = Browser()
    initial_actions = [
        {'open_tab': {'url': 'https://x.com/' + handle}},
    ]

    file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'twitter_cookies.txt')

    # Use script location as reference point for json file path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    json_file_path = os.path.join(script_dir, "../../../data/my_following.json")
    # Make the path absolute to resolve the relative components
    json_file_path = os.path.abspath(json_file_path)

    context = BrowserContext(browser=browser, config=BrowserContextConfig(cookies_file=file_path))

    controller = Controller()
    agent = Agent(
        task=(
            "Follow " + handle
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
            json.dump({"following": handle}, f, indent=2)
            print(f"Updated following saved to {json_file_path}")
    else:
        print('No result')
        return False
    return True

if __name__ == "__main__":
    asyncio.run(follow_user())