"""
Twitter Following System with Rate Limiting
Main following module that handles both single and bulk following operations
"""

import asyncio
import json
import os
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from browser_use import Agent, Browser, Controller
from browser_use.browser.context import BrowserContext
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from ..utils.cookie_manager import get_cookie_manager

load_dotenv()


@dataclass
class RateLimitTracker:
    """Tracks rate limits for following operations"""
    follows_today: int = 0
    follows_this_minute: int = 0
    last_follow_time: Optional[datetime] = None
    minute_reset_time: Optional[datetime] = None
    day_reset_time: Optional[datetime] = None


class TwitterFollower:
    """Main Twitter following system with rate limiting for single and bulk operations"""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize follower with configuration"""
        self.config = self._load_config(config_path)
        self.rate_tracker = RateLimitTracker()
        self._setup_rate_limits()
    
    def _load_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """Load configuration from config.json"""
        if config_path is None:
            # Search for config.json starting from current file location
            current_dir = os.path.dirname(os.path.abspath(__file__))
            config_path = os.path.join(current_dir, "../../../../config.json")
        
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            raise Exception(f"Error loading config from {config_path}: {e}")
    
    def _setup_rate_limits(self):
        """Setup rate limit configuration"""
        following_config = self.config.get("following", {})
        rate_limits = following_config.get("rate_limits", {})
        
        self.follows_per_minute = rate_limits.get("follows_per_minute", 15)
        self.follows_per_day = rate_limits.get("follows_per_day", 400)
        self.delay_between_follows = rate_limits.get("delay_between_follows", 4)
        
        retry_config = following_config.get("retry", {})
        self.max_attempts = retry_config.get("max_attempts", 3)
        self.delay_on_error = retry_config.get("delay_on_error", 10)
        
        self.accounts_file = following_config.get("accounts_file", "./accounts_to_follow.json")
        
        # Make accounts file path absolute if relative
        if not os.path.isabs(self.accounts_file):
            current_dir = os.path.dirname(os.path.abspath(__file__))
            self.accounts_file = os.path.join(current_dir, "../../../../", self.accounts_file)
    
    def load_accounts(self) -> List[Dict[str, Any]]:
        """Load accounts to follow from JSON file"""
        try:
            with open(self.accounts_file, 'r') as f:
                data = json.load(f)
                return data.get("accounts", [])
        except (FileNotFoundError, json.JSONDecodeError) as e:
            raise Exception(f"Error loading accounts from {self.accounts_file}: {e}")
    
    def _check_rate_limits(self) -> bool:
        """Check if we can follow another account based on rate limits"""
        now = datetime.now()
        
        # Reset daily counter if it's a new day
        if (self.rate_tracker.day_reset_time is None or 
            now >= self.rate_tracker.day_reset_time):
            self.rate_tracker.follows_today = 0
            self.rate_tracker.day_reset_time = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        
        # Reset minute counter if it's a new minute
        if (self.rate_tracker.minute_reset_time is None or 
            now >= self.rate_tracker.minute_reset_time):
            self.rate_tracker.follows_this_minute = 0
            self.rate_tracker.minute_reset_time = now.replace(second=0, microsecond=0) + timedelta(minutes=1)
        
        # Check daily limit
        if self.rate_tracker.follows_today >= self.follows_per_day:
            print(f"Daily limit reached ({self.follows_per_day}). Stopping for today.")
            return False
        
        # Check minute limit
        if self.rate_tracker.follows_this_minute >= self.follows_per_minute:
            wait_time = (self.rate_tracker.minute_reset_time - now).total_seconds()
            print(f"Minute limit reached ({self.follows_per_minute}). Waiting {wait_time:.1f} seconds...")
            time.sleep(wait_time + 1)  # Add 1 second buffer
            return self._check_rate_limits()  # Recheck after waiting
        
        return True
    
    def _wait_between_follows(self):
        """Wait the configured delay between follows"""
        if self.rate_tracker.last_follow_time:
            elapsed = (datetime.now() - self.rate_tracker.last_follow_time).total_seconds()
            if elapsed < self.delay_between_follows:
                wait_time = self.delay_between_follows - elapsed
                print(f"Waiting {wait_time:.1f} seconds before next follow...")
                time.sleep(wait_time)
    
    async def follow_single_account(self, handle: str) -> bool:
        """Follow a single account using browser automation"""
        # Ensure handle starts with @ for URL construction
        if not handle.startswith('@'):
            handle = '@' + handle
        
        # Remove @ for URL (Twitter URLs don't use @)
        url_handle = handle[1:] if handle.startswith('@') else handle
        
        try:
            browser = Browser()
            initial_actions = [
                {"open_tab": {"url": f"https://x.com/{url_handle}"}},
            ]

            cookie_manager = get_cookie_manager()
            context = BrowserContext(
                browser=browser, config=cookie_manager.create_browser_context_config()
            )

            controller = Controller()
            agent = Agent(
                task=f"Follow {handle}",
                llm=ChatOpenAI(model="gpt-4o"),
                save_conversation_path="logs/conversation",
                browser_context=context,
                initial_actions=initial_actions,
                max_actions_per_step=4,
                controller=controller,
            )
            
            history = await agent.run(max_steps=10)
            result = history.final_result()
            await browser.close()
            
            return result is not None
            
        except Exception as e:
            print(f"Error following {handle}: {e}")
            return False
    
    async def follow_user(self, handle: str) -> bool:
        """
        Follow a single user with rate limiting
        Main interface for following individual accounts
        """
        if not self._check_rate_limits():
            print("Rate limits exceeded. Cannot follow user at this time.")
            return False
        
        self._wait_between_follows()
        
        success = await self.follow_single_account(handle)
        
        if success:
            self.rate_tracker.follows_today += 1
            self.rate_tracker.follows_this_minute += 1
            self.rate_tracker.last_follow_time = datetime.now()
            print(f"✓ Successfully followed @{handle}")
        else:
            print(f"✗ Failed to follow @{handle}")
        
        return success


# Convenience functions for easy importing
_follower_instance = None

def get_follower() -> TwitterFollower:
    """Get global follower instance"""
    global _follower_instance
    if _follower_instance is None:
        _follower_instance = TwitterFollower()
    return _follower_instance

async def follow_user(handle: str) -> bool:
    """Convenience function to follow a single user"""
    follower = get_follower()
    return await follower.follow_user(handle)


if __name__ == "__main__":
    import sys
    
    async def main():
        if len(sys.argv) > 1:
            # Follow specific user from command line
            handle = sys.argv[1]
            print(f"Following user: {handle}")
            success = await follow_user(handle)
            print(f"Result: {'Success' if success else 'Failed'}")
        else:
            print("Usage: python follow_system.py <handle>")
            print("Example: python follow_system.py elonmusk")
    
    asyncio.run(main())
