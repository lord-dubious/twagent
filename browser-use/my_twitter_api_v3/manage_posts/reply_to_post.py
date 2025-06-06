import json
import os
import os.path
from datetime import datetime

from browser_use import Agent, Browser, Controller
from browser_use.browser.browser import Browser
from browser_use.browser.context import BrowserContext
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

from ..utils.cookie_manager import get_cookie_manager

load_dotenv()


async def reply_to_post(
    my_post="gross", tweet_url="https://x.com/SolJakey/status/1903232593254027508"
):
    browser = Browser()
    initial_actions = [
        {"open_tab": {"url": tweet_url}},
        {"scroll_down": {"amount": 200}},
    ]

    # Use cookie manager for centralized cookie handling
    cookie_manager = get_cookie_manager()

    # Use script location as reference point for json file path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    json_file_path = os.path.join(script_dir, "../../../data/003_posted_tweets.json")
    # Make the path absolute to resolve the relative components
    json_file_path = os.path.abspath(json_file_path)

    controller = Controller()
    context = BrowserContext(
        browser=browser, config=cookie_manager.create_browser_context_config()
    )

    agent = Agent(
        task=(
            "Reply to the tweet with: "
            + my_post
            + " and then make sure to click the reply button."
        ),
        llm=ChatOpenAI(model="gpt-4o-mini"),
        save_conversation_path="logs/conversation",  # Save chat logs
        browser_context=context,
        initial_actions=initial_actions,
        max_actions_per_step=4,
        controller=controller,
    )
    history = await agent.run(max_steps=10)
    result = history.final_result()
    if result:
        # Get current timestamp
        reply_time = datetime.now().isoformat()

        # Prepare data to save
        tweet_data = {
            "initial_tweet_url": tweet_url,
            "reply_text": my_post,
            "reply_time": reply_time,
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
        print("No result")
        return False
    return True


if __name__ == "__main__":
    reply_to_post()
