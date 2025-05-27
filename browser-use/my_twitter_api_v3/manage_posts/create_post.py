import json
import os
import os.path
from datetime import datetime

from browser_use import Agent, Browser, Controller
from browser_use.browser.browser import Browser
from browser_use.browser.context import BrowserContext
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()


async def create_post(
    tweet_url="https://pro.x.com/i/decks/1902192120082866405",
    my_post="I want mexican food right now.",
):
    browser = Browser()
    initial_actions = [
        {"open_tab": {"url": tweet_url}},
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
        task=("Post a tweet saying:" + my_post),
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
        reply_time = datetime.now().isoformat()

        # Prepare data to save
        tweet_data = {"reply_text": my_post, "reply_time": reply_time}

        with open(json_file_path, "w") as f:
            json.dump(tweet_data, f, indent=2)
            print(f"Updated tweet data saved to {json_file_path}")
    else:
        print("No result")


if __name__ == "__main__":
    create_post()
