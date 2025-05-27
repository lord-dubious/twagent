import json
import os
import os.path

from browser_use import Agent, Browser, Controller
from browser_use.browser.browser import Browser
from browser_use.browser.context import BrowserContext
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()


async def create_new_deck():
    browser = Browser()
    initial_actions = [
        {"open_tab": {"url": "https://pro.x.com"}},
    ]

    # Use cookie manager for centralized cookie handling
    cookie_manager = get_cookie_manager()

    # Use script location as reference point for json file path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    json_file_path = os.path.join(script_dir, "../../../data/decks.json")
    # Make the path absolute to resolve the relative components
    json_file_path = os.path.abspath(json_file_path)

    context = BrowserContext(
        browser=browser, config=cookie_manager.create_browser_context_config()
    )

    controller = Controller()
    deck_name = "koala"
    column_type = "explore"
    agent = Agent(
        task=(
            "Create a new deck. Name it "
            + deck_name
            + ". Add column. Set to "
            + column_type
            + "."
        ),
        llm=ChatOpenAI(model="gpt-4o"),
        save_conversation_path="logs/conversation",  # Save chat logs
        browser_context=context,
        initial_actions=initial_actions,
        max_actions_per_step=4,
        controller=controller,
    )
    history = await agent.run(max_steps=10)
    result = history.final_result()
    if result:
        with open(json_file_path, "w") as f:
            json.dump({"deck_name": deck_name, "column_type": column_type}, f, indent=2)
            print(f"Updated decks saved to {json_file_path}")
    else:
        print("No result")
        return False
    await browser.close()
    return True


if __name__ == "__main__":
    create_new_deck()
