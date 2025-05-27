from browser_use import Agent, Browser, Controller
from browser_use.browser.browser import Browser
from browser_use.browser.context import BrowserContext
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()


async def create_list(name="my_list"):
    browser = Browser()
    initial_actions = [
        {"open_tab": {"url": "https://x.com/i/lists/create"}},
    ]

    # Use cookie manager for centralized cookie handling
    cookie_manager = get_cookie_manager()

    context = BrowserContext(
        browser=browser, config=cookie_manager.create_browser_context_config()
    )

    controller = Controller()
    agent = Agent(
        task=(
            "Create a new list. Name the list: "
            + name
            + ". Make it private. Create it."
        ),
        llm=ChatOpenAI(model="gpt-4o"),
        save_conversation_path="logs/conversation",  # Save chat logs
        browser_context=context,
        initial_actions=initial_actions,
        max_actions_per_step=4,
        controller=controller,
    )
    history = await agent.run(max_steps=10)
    await browser.close()

    return True


if __name__ == "__main__":
    create_list()
