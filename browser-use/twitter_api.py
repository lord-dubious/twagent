#!/usr/bin/env python3
"""
Twitter API Module

This module provides a unified interface for Twitter API operations using browser automation.
All API methods are consolidated in this file, with prompts and browser settings modularized.
"""

import json
import os
import os.path
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, TypeVar, Type
from pathlib import Path

from browser_use import Agent, Browser, Controller
from browser_use.browser.browser import Browser
from browser_use.browser.context import BrowserContext, BrowserContextConfig
from browser_use.agent.views import AgentHistoryList
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from pydantic import BaseModel

load_dotenv()

# Type variable for generic return types
T = TypeVar('T')

# ============================================================================
# Data Models
# ============================================================================

class Tweet(BaseModel):
    """Model for tweet data"""
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


# ============================================================================
# Configuration and Settings
# ============================================================================

class TwitterAPIConfig:
    """Configuration for Twitter API operations"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize Twitter API configuration
        
        Args:
            config_path: Path to config.json file (optional)
        """
        self.config = self._load_config(config_path)
        self.data_dir = self._resolve_data_dir()
        self.cookie_file_path = self._resolve_cookie_path()
        self.llm_model = self.config.get("llm", {}).get("model", "gpt-4o")
        self.llm_temperature = self.config.get("llm", {}).get("temperature", 0.7)
        
        # Ensure data directory exists
        os.makedirs(self.data_dir, exist_ok=True)
    
    def _load_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """Load configuration from config.json"""
        if config_path is None:
            # Search for config.json starting from current file location
            current_dir = Path(__file__).parent
            
            # Try different locations
            possible_paths = [
                current_dir / "../config.json",      # From browser-use/ to project root
                current_dir / "../../config.json",   # Alternative path
                Path.cwd() / "config.json",          # Current working directory
            ]
            
            for path in possible_paths:
                if path.exists():
                    config_path = str(path.resolve())
                    break
            else:
                # Default configuration if no config file found
                return {
                    "cookies": {"file_path": "./cookies.json"},
                    "data": {"directory": "./data"},
                    "llm": {"model": "gpt-4o", "temperature": 0.7}
                }
        
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error loading config from {config_path}: {e}")
            # Default configuration if error loading config file
            return {
                "cookies": {"file_path": "./cookies.json"},
                "data": {"directory": "./data"},
                "llm": {"model": "gpt-4o", "temperature": 0.7}
            }
    
    def _resolve_data_dir(self) -> str:
        """Resolve the absolute path to the data directory"""
        data_dir = self.config.get("data", {}).get("directory", "./data")
        
        # If relative path, make it relative to config file location
        if not os.path.isabs(data_dir):
            config_dir = Path(__file__).parent / "../"
            data_dir = str((config_dir / data_dir).resolve())
        
        return data_dir
    
    def _resolve_cookie_path(self) -> str:
        """Resolve the absolute path to the cookie file"""
        cookie_path = self.config.get("cookies", {}).get("file_path", "./cookies.json")
        
        # If relative path, make it relative to config file location
        if not os.path.isabs(cookie_path):
            config_dir = Path(__file__).parent / "../"
            cookie_path = str((config_dir / cookie_path).resolve())
        
        return cookie_path
    
    def get_data_file_path(self, filename: str) -> str:
        """Get the absolute path to a data file"""
        return os.path.join(self.data_dir, filename)
    
    def create_browser_context_config(self, **kwargs) -> BrowserContextConfig:
        """
        Create a BrowserContextConfig with the cookie file path
        
        Args:
            **kwargs: Additional arguments to pass to BrowserContextConfig
        
        Returns:
            BrowserContextConfig instance with cookies configured
        """
        return BrowserContextConfig(
            cookies_file=self.cookie_file_path,
            **kwargs
        )
    
    def get_llm(self) -> ChatOpenAI:
        """Get a ChatOpenAI instance with configured settings"""
        return ChatOpenAI(
            model=self.llm_model,
            temperature=self.llm_temperature
        )


# Global configuration instance
_twitter_config = None

def get_twitter_config(config_path: Optional[str] = None) -> TwitterAPIConfig:
    """
    Get the global Twitter API configuration instance
    
    Args:
        config_path: Path to config.json file (only used on first call)
    
    Returns:
        TwitterAPIConfig instance
    """
    global _twitter_config
    if _twitter_config is None:
        _twitter_config = TwitterAPIConfig(config_path)
    return _twitter_config


# ============================================================================
# Prompt Templates
# ============================================================================

class PromptTemplates:
    """Templates for Twitter API operations"""
    
    @staticmethod
    def get_tweet_prompt() -> str:
        """Get prompt for retrieving tweet data"""
        return (
            "Extract the tweet's: text, likes total, retweet total, reply total, "
            "bookmark total, tweet_link, the author's handle, the datetime it was posted, "
            "and its viewcount"
        )
    
    @staticmethod
    def create_post_prompt(post_text: str) -> str:
        """Get prompt for creating a post"""
        return f"Post a tweet saying: {post_text}"
    
    @staticmethod
    def reply_to_post_prompt(reply_text: str) -> str:
        """Get prompt for replying to a post"""
        return f"Reply to this tweet with: {reply_text}"
    
    @staticmethod
    def follow_user_prompt(username: str) -> str:
        """Get prompt for following a user"""
        return f"Follow the Twitter user @{username}"
    
    @staticmethod
    def block_user_prompt(username: str) -> str:
        """Get prompt for blocking a user"""
        return f"Block the Twitter user @{username}"
    
    @staticmethod
    def create_list_prompt(list_name: str, description: str) -> str:
        """Get prompt for creating a list"""
        return f"Create a Twitter list named '{list_name}' with description: {description}"
    
    @staticmethod
    def add_members_to_list_prompt(list_name: str, usernames: List[str]) -> str:
        """Get prompt for adding members to a list"""
        usernames_str = ", ".join([f"@{username}" for username in usernames])
        return f"Add these users to the Twitter list '{list_name}': {usernames_str}"
    
    @staticmethod
    def get_list_posts_prompt(list_name: str) -> str:
        """Get prompt for getting posts from a list"""
        return f"Get the most recent posts from the Twitter list '{list_name}'"


# ============================================================================
# Browser Session Management
# ============================================================================

class TwitterBrowserSession:
    """Manages browser sessions for Twitter API operations"""
    
    def __init__(self, 
                config: Optional[TwitterAPIConfig] = None,
                browser: Optional[Browser] = None,
                browser_context: Optional[BrowserContext] = None):
        """
        Initialize Twitter browser session
        
        Args:
            config: TwitterAPIConfig instance (optional)
            browser: Existing Browser instance to reuse (optional)
            browser_context: Existing BrowserContext to reuse (optional)
        """
        self.config = config or get_twitter_config()
        self.browser = browser
        self.context = browser_context
        self.should_close_browser = browser is None
    
    async def __aenter__(self):
        """Set up browser session when entering context"""
        if self.browser is None:
            self.browser = Browser()
            
        if self.context is None:
            self.context = BrowserContext(
                browser=self.browser,
                config=self.config.create_browser_context_config()
            )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Clean up browser session when exiting context"""
        if self.should_close_browser and self.browser:
            await self.browser.close()
    
    def create_agent(self, 
                    task: str, 
                    initial_actions: List[Dict[str, Any]],
                    output_model: Optional[Type[T]] = None,
                    max_actions_per_step: int = 6,
                    max_steps: int = 10) -> Agent:
        """
        Create an agent for Twitter operations
        
        Args:
            task: Task description for the agent
            initial_actions: Initial actions for the agent
            output_model: Output model for the agent (optional)
            max_actions_per_step: Maximum actions per step
            max_steps: Maximum steps
            
        Returns:
            Agent instance
        """
        controller = Controller(output_model=output_model) if output_model else Controller()
        
        return Agent(
            task=task,
            llm=self.config.get_llm(),
            save_conversation_path="logs/conversation",
            browser_context=self.context,
            initial_actions=initial_actions,
            max_actions_per_step=max_actions_per_step,
            controller=controller,
        )


# ============================================================================
# Twitter API Methods
# ============================================================================

async def get_tweet(post_url: str) -> Optional[Tweet]:
    """
    Get tweet data from a URL
    
    Args:
        post_url: URL of the tweet
        
    Returns:
        Tweet object or None if retrieval failed
    """
    config = get_twitter_config()
    initial_actions = [
        {"open_tab": {"url": post_url}},
    ]
    
    try:
        async with TwitterBrowserSession(config) as session:
            agent = session.create_agent(
                task=PromptTemplates.get_tweet_prompt(),
                initial_actions=initial_actions,
                output_model=Tweet,
                max_steps=6
            )
            
            history = await agent.run()
            result = history.final_result()
            
            if result:
                parsed_tweet = Tweet.model_validate_json(result)
                
                # Save tweet data
                try:
                    # Load existing tweets from JSON file if it exists
                    tweets_file = config.get_data_file_path("001_saved_tweets.json")
                    existing_tweets = []
                    
                    try:
                        with open(tweets_file, "r") as f:
                            data = json.load(f)
                            existing_tweets = data.get("tweets", [])
                    except (FileNotFoundError, json.JSONDecodeError):
                        existing_tweets = []
                    
                    # Create a dictionary representation of the tweet
                    tweet_dict = {
                        "handle": parsed_tweet.handle,
                        "datetime": parsed_tweet.datetime,
                        "text": parsed_tweet.text,
                        "likes": parsed_tweet.likes,
                        "retweets": parsed_tweet.retweets,
                        "replies": parsed_tweet.replies,
                        "bookmarks": parsed_tweet.bookmarks,
                        "tweet_url": post_url,
                        "viewcount": parsed_tweet.viewcount,
                    }
                    
                    # Check if the tweet's URL matches the post_url and update or add it
                    updated = False
                    for i, existing in enumerate(existing_tweets):
                        if existing["tweet_url"] == tweet_dict["tweet_url"]:
                            existing_tweets[i] = tweet_dict
                            updated = True
                            print(f"Updated tweet from {tweet_dict['handle']} at {post_url}")
                            break
                    
                    if not updated:
                        existing_tweets.append(tweet_dict)
                        print(f"Added new tweet from {tweet_dict['handle']} at {post_url}")
                    
                    # Save updated tweets list
                    with open(tweets_file, "w") as f:
                        json.dump({"tweets": existing_tweets}, f, indent=2)
                        print("Updated tweets saved.")
                
                except Exception as e:
                    print(f"Error saving tweet data: {e}")
                
                return parsed_tweet
    except Exception as e:
        print(f"Error retrieving tweet: {e}")
    
    return None


async def create_post(post_text: str, media_path: Optional[str] = None) -> bool:
    """
    Create a new post on Twitter
    
    Args:
        post_text: Text content of the post
        media_path: Path to media file to include (optional)
        
    Returns:
        True if successful, False otherwise
    """
    config = get_twitter_config()
    initial_actions = [
        {"open_tab": {"url": "https://x.com/home"}},
    ]
    
    try:
        async with TwitterBrowserSession(config) as session:
            task = PromptTemplates.create_post_prompt(post_text)
            
            # If media is provided, add it to the task description
            if media_path:
                if os.path.exists(media_path):
                    task += f" and attach the media file from {media_path}"
                else:
                    print(f"Warning: Media file not found at {media_path}")
            
            agent = session.create_agent(
                task=task,
                initial_actions=initial_actions,
                max_steps=10
            )
            
            history = await agent.run()
            result = history.final_result()
            
            if result:
                # Save post data
                try:
                    post_time = datetime.now().isoformat()
                    post_data = {
                        "post_text": post_text,
                        "post_time": post_time,
                        "media_path": media_path
                    }
                    
                    posts_file = config.get_data_file_path("003_posted_tweets.json")
                    
                    # Load existing posts if file exists
                    existing_data = {}
                    try:
                        with open(posts_file, "r") as f:
                            existing_data = json.load(f)
                    except (FileNotFoundError, json.JSONDecodeError):
                        existing_data = {}
                    
                    # Initialize posts list if it doesn't exist
                    if "posts" not in existing_data:
                        existing_data["posts"] = []
                    
                    # Add new post
                    existing_data["posts"].append(post_data)
                    
                    # Save updated posts list
                    with open(posts_file, "w") as f:
                        json.dump(existing_data, f, indent=2)
                        print(f"Post data saved to {posts_file}")
                
                except Exception as e:
                    print(f"Error saving post data: {e}")
                
                return True
    except Exception as e:
        print(f"Error creating post: {e}")
    
    return False


async def reply_to_post(post_url: str, reply_text: str, media_path: Optional[str] = None) -> bool:
    """
    Reply to a post on Twitter
    
    Args:
        post_url: URL of the post to reply to
        reply_text: Text content of the reply
        media_path: Path to media file to include (optional)
        
    Returns:
        True if successful, False otherwise
    """
    config = get_twitter_config()
    initial_actions = [
        {"open_tab": {"url": post_url}},
    ]
    
    async with TwitterBrowserSession(config) as session:
        task = PromptTemplates.reply_to_post_prompt(reply_text)
        
        # If media is provided, add it to the task description
        if media_path:
            task += f" and attach the media file from {media_path}"
        
        agent = session.create_agent(
            task=task,
            initial_actions=initial_actions
        )
        
        history = await agent.run(max_steps=10)
        result = history.final_result()
        
        if result:
            # Save reply data
            try:
                reply_time = datetime.now().isoformat()
                reply_data = {
                    "post_url": post_url,
                    "reply_text": reply_text,
                    "reply_time": reply_time,
                    "media_path": media_path
                }
                
                replies_file = config.get_data_file_path("003_posted_tweets.json")
                
                # Load existing replies if file exists
                existing_data = {}
                try:
                    with open(replies_file, "r") as f:
                        existing_data = json.load(f)
                except (FileNotFoundError, json.JSONDecodeError):
                    existing_data = {}
                
                # Initialize replies list if it doesn't exist
                if "replies" not in existing_data:
                    existing_data["replies"] = []
                
                # Add new reply
                existing_data["replies"].append(reply_data)
                
                # Save updated replies list
                with open(replies_file, "w") as f:
                    json.dump(existing_data, f, indent=2)
                    print(f"Reply data saved to {replies_file}")
            
            except Exception as e:
                print(f"Error saving reply data: {e}")
            
            return True
        
        return False


async def follow_user(username: str) -> bool:
    """
    Follow a user on Twitter
    
    Args:
        username: Username of the user to follow
        
    Returns:
        True if successful, False otherwise
    """
    config = get_twitter_config()
    initial_actions = [
        {"open_tab": {"url": f"https://x.com/{username}"}},
    ]
    
    async with TwitterBrowserSession(config) as session:
        agent = session.create_agent(
            task=PromptTemplates.follow_user_prompt(username),
            initial_actions=initial_actions
        )
        
        history = await agent.run(max_steps=6)
        result = history.final_result()
        
        if result:
            # Save follow data
            try:
                follow_time = datetime.now().isoformat()
                follow_data = {
                    "username": username,
                    "follow_time": follow_time
                }
                
                follows_file = config.get_data_file_path("004_users.json")
                
                # Load existing follows if file exists
                existing_data = {}
                try:
                    with open(follows_file, "r") as f:
                        existing_data = json.load(f)
                except (FileNotFoundError, json.JSONDecodeError):
                    existing_data = {}
                
                # Initialize follows list if it doesn't exist
                if "follows" not in existing_data:
                    existing_data["follows"] = []
                
                # Check if user is already in follows list
                for i, existing in enumerate(existing_data["follows"]):
                    if existing["username"] == username:
                        existing_data["follows"][i] = follow_data
                        print(f"Updated follow data for @{username}")
                        break
                else:
                    # Add new follow
                    existing_data["follows"].append(follow_data)
                    print(f"Added follow data for @{username}")
                
                # Save updated follows list
                with open(follows_file, "w") as f:
                    json.dump(existing_data, f, indent=2)
                    print(f"Follow data saved to {follows_file}")
            
            except Exception as e:
                print(f"Error saving follow data: {e}")
            
            return True
        
        return False


async def block_user(username: str) -> bool:
    """
    Block a user on Twitter
    
    Args:
        username: Username of the user to block
        
    Returns:
        True if successful, False otherwise
    """
    config = get_twitter_config()
    initial_actions = [
        {"open_tab": {"url": f"https://x.com/{username}"}},
    ]
    
    async with TwitterBrowserSession(config) as session:
        agent = session.create_agent(
            task=PromptTemplates.block_user_prompt(username),
            initial_actions=initial_actions
        )
        
        history = await agent.run(max_steps=6)
        result = history.final_result()
        
        if result:
            # Save block data
            try:
                block_time = datetime.now().isoformat()
                block_data = {
                    "username": username,
                    "block_time": block_time
                }
                
                blocks_file = config.get_data_file_path("004_users.json")
                
                # Load existing blocks if file exists
                existing_data = {}
                try:
                    with open(blocks_file, "r") as f:
                        existing_data = json.load(f)
                except (FileNotFoundError, json.JSONDecodeError):
                    existing_data = {}
                
                # Initialize blocks list if it doesn't exist
                if "blocks" not in existing_data:
                    existing_data["blocks"] = []
                
                # Check if user is already in blocks list
                for i, existing in enumerate(existing_data["blocks"]):
                    if existing["username"] == username:
                        existing_data["blocks"][i] = block_data
                        print(f"Updated block data for @{username}")
                        break
                else:
                    # Add new block
                    existing_data["blocks"].append(block_data)
                    print(f"Added block data for @{username}")
                
                # Save updated blocks list
                with open(blocks_file, "w") as f:
                    json.dump(existing_data, f, indent=2)
                    print(f"Block data saved to {blocks_file}")
            
            except Exception as e:
                print(f"Error saving block data: {e}")
            
            return True
        
        return False


async def create_list(list_name: str, description: str) -> bool:
    """
    Create a new list on Twitter
    
    Args:
        list_name: Name of the list
        description: Description of the list
        
    Returns:
        True if successful, False otherwise
    """
    config = get_twitter_config()
    initial_actions = [
        {"open_tab": {"url": "https://x.com/lists"}},
    ]
    
    async with TwitterBrowserSession(config) as session:
        agent = session.create_agent(
            task=PromptTemplates.create_list_prompt(list_name, description),
            initial_actions=initial_actions
        )
        
        history = await agent.run(max_steps=10)
        result = history.final_result()
        
        if result:
            # Save list data
            try:
                list_time = datetime.now().isoformat()
                list_data = {
                    "name": list_name,
                    "description": description,
                    "created_time": list_time,
                    "members": []
                }
                
                lists_file = config.get_data_file_path("005_lists.json")
                
                # Load existing lists if file exists
                existing_data = {}
                try:
                    with open(lists_file, "r") as f:
                        existing_data = json.load(f)
                except (FileNotFoundError, json.JSONDecodeError):
                    existing_data = {}
                
                # Initialize lists list if it doesn't exist
                if "lists" not in existing_data:
                    existing_data["lists"] = []
                
                # Check if list already exists
                for i, existing in enumerate(existing_data["lists"]):
                    if existing["name"] == list_name:
                        existing_data["lists"][i] = list_data
                        print(f"Updated list data for '{list_name}'")
                        break
                else:
                    # Add new list
                    existing_data["lists"].append(list_data)
                    print(f"Added list data for '{list_name}'")
                
                # Save updated lists list
                with open(lists_file, "w") as f:
                    json.dump(existing_data, f, indent=2)
                    print(f"List data saved to {lists_file}")
            
            except Exception as e:
                print(f"Error saving list data: {e}")
            
            return True
        
        return False


async def add_members_to_list(list_name: str, usernames: List[str]) -> bool:
    """
    Add members to a list on Twitter
    
    Args:
        list_name: Name of the list
        usernames: List of usernames to add
        
    Returns:
        True if successful, False otherwise
    """
    config = get_twitter_config()
    initial_actions = [
        {"open_tab": {"url": "https://x.com/lists"}},
    ]
    
    async with TwitterBrowserSession(config) as session:
        agent = session.create_agent(
            task=PromptTemplates.add_members_to_list_prompt(list_name, usernames),
            initial_actions=initial_actions
        )
        
        history = await agent.run(max_steps=10)
        result = history.final_result()
        
        if result:
            # Update list data
            try:
                lists_file = config.get_data_file_path("005_lists.json")
                
                # Load existing lists if file exists
                existing_data = {}
                try:
                    with open(lists_file, "r") as f:
                        existing_data = json.load(f)
                except (FileNotFoundError, json.JSONDecodeError):
                    existing_data = {}
                
                # Initialize lists list if it doesn't exist
                if "lists" not in existing_data:
                    existing_data["lists"] = []
                
                # Find the list and update members
                list_found = False
                for i, existing in enumerate(existing_data["lists"]):
                    if existing["name"] == list_name:
                        # Add new members to the list
                        existing_members = set(existing["members"])
                        for username in usernames:
                            existing_members.add(username)
                        
                        existing_data["lists"][i]["members"] = list(existing_members)
                        list_found = True
                        print(f"Updated members for list '{list_name}'")
                        break
                
                if not list_found:
                    # Create new list if it doesn't exist
                    list_data = {
                        "name": list_name,
                        "description": "",
                        "created_time": datetime.now().isoformat(),
                        "members": usernames
                    }
                    existing_data["lists"].append(list_data)
                    print(f"Created new list '{list_name}' with members")
                
                # Save updated lists list
                with open(lists_file, "w") as f:
                    json.dump(existing_data, f, indent=2)
                    print(f"List data saved to {lists_file}")
            
            except Exception as e:
                print(f"Error updating list data: {e}")
            
            return True
        
        return False


async def get_list_posts(list_name: str) -> bool:
    """
    Get posts from a list on Twitter
    
    Args:
        list_name: Name of the list
        
    Returns:
        True if successful, False otherwise
    """
    config = get_twitter_config()
    initial_actions = [
        {"open_tab": {"url": "https://x.com/lists"}},
    ]
    
    async with TwitterBrowserSession(config) as session:
        agent = session.create_agent(
            task=PromptTemplates.get_list_posts_prompt(list_name),
            initial_actions=initial_actions
        )
        
        history = await agent.run(max_steps=10)
        result = history.final_result()
        
        if result:
            # Process and save list posts data
            # This would typically involve parsing the posts and saving them
            # For now, we'll just return success
            return True
        
        return False


# ============================================================================
# Main Function
# ============================================================================

if __name__ == "__main__":
    import asyncio
    
    async def main():
        """Example usage of the Twitter API"""
        print("Twitter API Example")
        print("===================")
        
        # Example 1: Get a tweet
        print("\n1. Getting a tweet...")
        tweet_url = "https://twitter.com/TheBabylonBee/status/1903616058562576739"
        tweet = await get_tweet(tweet_url)
        
        if tweet:
            print(f"✅ Retrieved tweet from @{tweet.handle}:")
            print(f"Text: {tweet.text}")
            print(f"Likes: {tweet.likes}")
            print(f"Retweets: {tweet.retweets}")
        else:
            print("❌ Failed to retrieve tweet.")
        
        # Example 2: Create a post (commented out to avoid actual posting)
        """
        print("\n2. Creating a post...")
        success = await create_post("Testing the Twitter API from browser-use")
        
        if success:
            print("✅ Post created successfully!")
        else:
            print("❌ Failed to create post.")
        """
        
        # Example 3: Reusing browser session
        print("\n3. Demonstrating browser session reuse...")
        config = get_twitter_config()
        browser = Browser()
        
        try:
            # First operation with shared browser
            async with TwitterBrowserSession(config, browser=browser) as session1:
                print("  First operation with shared browser...")
                # Just a placeholder operation
                pass
                
            # Second operation with same browser
            async with TwitterBrowserSession(config, browser=browser) as session2:
                print("  Second operation with same browser...")
                # Just a placeholder operation
                pass
                
            print("✅ Browser session reuse successful!")
        except Exception as e:
            print(f"❌ Error during browser session reuse: {e}")
        finally:
            # Clean up the browser
            await browser.close()
            print("  Browser closed.")
        
        print("\nAll examples completed.")
    
    asyncio.run(main())
