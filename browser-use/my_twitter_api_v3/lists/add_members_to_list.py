from langchain_openai import ChatOpenAI
from browser_use import Agent, Browser
from pydantic import SecretStr
from pydantic import BaseModel

from browser_use import Agent, ActionResult, Controller
from browser_use.browser.browser import Browser, BrowserConfig
from browser_use.browser.context import BrowserContext, BrowserContextConfig

import  os
import asyncio
from dotenv import load_dotenv
import json
import os.path
from datetime import datetime

load_dotenv()

async def add_members_to_list(name = "my_list", handle=None, membersToAdd=[]):

    browser = Browser()
    initial_actions = [
        {'open_tab': {'url': 'https://x.com/'+ handle +'/lists'}},
    ]

    file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'twitter_cookies.txt')

    context = BrowserContext(browser=browser, config=BrowserContextConfig(cookies_file=file_path))

    controller = Controller()
    agent = Agent(
        task=(
            "Select the list with the name " + name + ". Select 'Edit List'. Select 'Manage members'. Go to the 'Suggested' tab. In the search people bar, search and add the following people, one at a time. Only add the person with the exact handle," + 
            str([handle[1:] for handle in membersToAdd])
        ),#remove the @ from the handle
        llm=ChatOpenAI(model="gpt-4o-mini"),
        save_conversation_path="logs/conversation",  # Save chat logs
		browser_context=context,
        initial_actions=initial_actions,
        max_actions_per_step=4,
        controller=controller
    )
    history = await agent.run(max_steps=100)
    await browser.close()

    return True

if __name__ == "__main__":
    add_members_to_list()