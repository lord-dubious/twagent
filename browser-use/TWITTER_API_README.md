# Twitter API Module

This module provides a unified interface for Twitter API operations using browser automation. All API methods are consolidated in a single file, with prompts and browser settings modularized.

## Features

- **Unified API**: All Twitter API methods in a single file
- **Modular Design**: Prompts and browser settings are modularized
- **Configuration**: Centralized configuration management
- **Data Storage**: Consistent data storage for all operations
- **Error Handling**: Robust error handling and logging
- **Browser Reuse**: Support for reusing browser sessions across operations
- **Type Safety**: Improved type annotations for better IDE support

## Installation

No additional installation is required beyond the main project dependencies.

## Usage

### Basic Usage

```python
import asyncio
from browser_use.twitter_api import get_tweet, create_post, follow_user

async def main():
    # Get a tweet
    tweet = await get_tweet("https://twitter.com/username/status/123456789")
    print(f"Tweet text: {tweet.text}")
    
    # Create a post
    success = await create_post("Hello, Twitter!")
    print(f"Post created: {success}")
    
    # Follow a user
    success = await follow_user("elonmusk")
    print(f"User followed: {success}")

asyncio.run(main())
```

### Browser Session Reuse

You can reuse browser sessions across multiple operations for better performance:

```python
import asyncio
from browser_use.twitter_api import TwitterBrowserSession, get_twitter_config, Browser

async def main():
    config = get_twitter_config()
    browser = Browser()
    
    try:
        # First operation with shared browser
        async with TwitterBrowserSession(config, browser=browser) as session1:
            agent = session1.create_agent(
                task="Extract the tweet's text and author",
                initial_actions=[{"open_tab": {"url": "https://twitter.com/username/status/123456789"}}],
                max_steps=6
            )
            history = await agent.run()
            
        # Second operation with same browser
        async with TwitterBrowserSession(config, browser=browser) as session2:
            agent = session2.create_agent(
                task="Visit Twitter home page",
                initial_actions=[{"open_tab": {"url": "https://x.com/home"}}],
                max_steps=3
            )
            history = await agent.run()
    finally:
        # Clean up the browser
        await browser.close()

asyncio.run(main())
```

### Configuration

The API uses a centralized configuration system. By default, it looks for a `config.json` file in the project root directory. You can also specify a custom configuration path:

```python
from browser_use.twitter_api import get_twitter_config

# Get the default configuration
config = get_twitter_config()

# Get configuration with a custom path
config = get_twitter_config("path/to/custom/config.json")
```

Example `config.json`:

```json
{
  "cookies": {
    "file_path": "./cookies.json"
  },
  "data": {
    "directory": "./data"
  },
  "llm": {
    "model": "gpt-4o",
    "temperature": 0.7
  }
}
```

## API Reference

### Tweet Operations

#### `get_tweet(post_url: str) -> Optional[Tweet]`

Get tweet data from a URL.

```python
tweet = await get_tweet("https://twitter.com/username/status/123456789")
```

#### `create_post(post_text: str, media_path: Optional[str] = None) -> bool`

Create a new post on Twitter.

```python
# Text-only post
success = await create_post("Hello, Twitter!")

# Post with media
success = await create_post("Check out this photo!", "path/to/image.jpg")
```

#### `reply_to_post(post_url: str, reply_text: str, media_path: Optional[str] = None) -> bool`

Reply to a post on Twitter.

```python
# Text-only reply
success = await reply_to_post("https://twitter.com/username/status/123456789", "Great post!")

# Reply with media
success = await reply_to_post("https://twitter.com/username/status/123456789", "Check this out!", "path/to/image.jpg")
```

### User Operations

#### `follow_user(username: str) -> bool`

Follow a user on Twitter.

```python
success = await follow_user("elonmusk")
```

#### `block_user(username: str) -> bool`

Block a user on Twitter.

```python
success = await block_user("spam_account")
```

### List Operations

#### `create_list(list_name: str, description: str) -> bool`

Create a new list on Twitter.

```python
success = await create_list("Tech News", "Latest tech news and updates")
```

#### `add_members_to_list(list_name: str, usernames: List[str]) -> bool`

Add members to a list on Twitter.

```python
success = await add_members_to_list("Tech News", ["elonmusk", "satyanadella", "sundarpichai"])
```

#### `get_list_posts(list_name: str) -> bool`

Get posts from a list on Twitter.

```python
success = await get_list_posts("Tech News")
```

## Data Models

### Tweet

```python
class Tweet(BaseModel):
    handle: str | None
    display_name: str | None
    text: str | None
    likes: int | None
    retweets: int | None
    replies: int | None
    bookmarks: int | None
    tweet_link: str | None
    viewcount: int | None
    datetime: str | None
```

## Advanced Usage

### Custom Browser Session

You can create a custom browser session for more complex operations:

```python
from browser_use.twitter_api import TwitterBrowserSession, get_twitter_config

async def custom_operation():
    config = get_twitter_config()
    
    async with TwitterBrowserSession(config) as session:
        # Create a custom agent
        agent = session.create_agent(
            task="Custom Twitter task",
            initial_actions=[{"open_tab": {"url": "https://x.com/home"}}]
        )
        
        # Run the agent
        history = await agent.run()
        
        return history.final_result()
```

### Custom Prompts

You can create custom prompts for specialized operations:

```python
from browser_use.twitter_api import PromptTemplates

# Use an existing prompt template
prompt = PromptTemplates.create_post_prompt("Hello, Twitter!")

# Create a custom prompt template
class CustomPromptTemplates(PromptTemplates):
    @staticmethod
    def custom_operation_prompt(parameter: str) -> str:
        return f"Perform custom operation with {parameter}"
```

## Error Handling

All API methods include comprehensive error handling:

- Top-level try/except blocks catch and log all exceptions
- Tweet operations return `None` or `False` on failure
- User operations return `False` on failure
- List operations return `False` on failure
- Detailed error messages are printed to the console

## Data Storage

The API automatically stores data in JSON files in the configured data directory:

- `001_saved_tweets.json`: Saved tweets
- `003_posted_tweets.json`: Posted tweets and replies
- `004_users.json`: Followed and blocked users
- `005_lists.json`: Created lists and their members

## Browser-Use Compatibility

This API is fully compatible with the browser-use Python package:

- Uses the Agent, Browser, and Controller classes correctly
- Properly manages browser contexts and sessions
- Supports all browser-use features like vision capabilities
- Follows browser-use best practices for resource management

## Contributing

To extend the API with new functionality:

1. Add a new method to the `twitter_api.py` file
2. Add a new prompt template to the `PromptTemplates` class
3. Update the README with documentation for the new method
