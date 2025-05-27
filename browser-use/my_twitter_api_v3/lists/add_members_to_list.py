from browser_use import Agent, Browser, Controller
from browser_use.browser.browser import Browser
from browser_use.browser.context import BrowserContext
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()


async def add_members_to_list(name="my_list", handle=None, membersToAdd=[]):
    browser = Browser()
    initial_actions = [
        {"open_tab": {"url": "https://x.com/" + handle + "/lists"}},
    ]

    # Use cookie manager for centralized cookie handling
    cookie_manager = get_cookie_manager()

    context = BrowserContext(
        browser=browser, config=cookie_manager.create_browser_context_config()
    )

    controller = Controller()
    agent = Agent(
        task=(
            "Select the list with the name "
            + name
            + ". Select 'Edit List'. Select 'Manage members'. Go to the 'Suggested' tab. In the search people bar, search and add the following people, one at a time. Only add the person with the exact handle,"
            + str([handle[1:] for handle in membersToAdd])
        ),  # remove the @ from the handle
        llm=ChatOpenAI(model="gpt-4o-mini"),
        save_conversation_path="logs/conversation",  # Save chat logs
        browser_context=context,
        initial_actions=initial_actions,
        max_actions_per_step=4,
        controller=controller,
    )
    history = await agent.run(max_steps=100)
    await browser.close()

    return True


if __name__ == "__main__":
    add_members_to_list()
