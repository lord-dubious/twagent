#!/usr/bin/env python3
"""
X.com Follower Automation

This script automates the process of following users who are followers of a specified target account.
It uses browser automation to navigate to a target user's followers page and follow users.

Features:
- Target specific user's followers
- Set follow goals and limits
- Randomized delays to avoid detection
- Automatic page refreshing when needed
- Detailed reporting
"""

import argparse
import asyncio
import json
import os
import random
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any

from browser_use import Agent, Browser, Controller
from browser_use.browser.context import BrowserContext
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

from my_twitter_api_v3.utils.cookie_manager import get_cookie_manager

load_dotenv()


class XFollowerAutomation:
    """
    Automates the process of following users who are followers of a target account on X.com
    """

    def __init__(
        self,
        target_username: str,
        follow_goal: int,
        max_refreshes: int = 10,
        config_path: Optional[str] = None,
    ):
        """
        Initialize the X.com follower automation

        Args:
            target_username: Username of the account whose followers to follow (without @)
            follow_goal: Number of new follows to complete
            max_refreshes: Maximum number of page refreshes before stopping
            config_path: Path to configuration file (optional)
        """
        self.target_username = target_username.lstrip('@')  # Remove @ if present
        self.follow_goal = follow_goal
        self.max_refreshes = max_refreshes
        self.config = self._load_config(config_path)
        
        # Initialize counters and tracking variables
        self.follows_completed = 0
        self.refresh_count = 0
        self.start_time = None
        self.end_time = None
        
        # Load safety settings
        self._load_safety_settings()
        
        # Results tracking
        self.results = {
            "follows_completed": 0,
            "refreshes_performed": 0,
            "time_taken": None,
            "status": "Not Started",
            "details": []
        }

    def _load_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """Load configuration from config.json"""
        if config_path is None:
            # Search for config.json starting from current file location
            current_dir = os.path.dirname(os.path.abspath(__file__))
            config_path = os.path.join(current_dir, "../../config.json")
        
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error loading config from {config_path}: {e}")
            return {}
    
    def _load_safety_settings(self):
        """Load safety settings from config or use defaults"""
        following_config = self.config.get("following", {})
        safety = following_config.get("safety", {})
        
        # Delay settings
        self.min_delay_between_follows = safety.get("min_delay_between_follows", 2)
        self.max_delay_between_follows = safety.get("max_delay_between_follows", 4)
        self.page_load_delay = safety.get("page_load_delay", 5)
        self.scroll_delay = safety.get("scroll_delay", 4)
        self.error_delay = safety.get("error_delay", 10)
        
        # Batch settings
        self.max_follows_per_page = safety.get("max_follows_per_page", 20)
        
        # Rate limits
        rate_limits = following_config.get("rate_limits", {})
        self.follows_per_minute = rate_limits.get("follows_per_minute", 15)
        self.follows_per_day = rate_limits.get("follows_per_day", 400)

    async def _navigate_to_followers_page(self, browser, context) -> bool:
        """
        Navigate to the target user's followers page
        
        Returns:
            bool: True if navigation was successful, False otherwise
        """
        try:
            # Create initial actions to navigate to target user's profile
            initial_actions = [
                {"open_tab": {"url": f"https://x.com/{self.target_username}"}},
            ]
            
            # Create agent to navigate to followers page
            controller = Controller()
            agent = Agent(
                task=f"Navigate to {self.target_username}'s followers page",
                llm=ChatOpenAI(model="gpt-4o"),
                save_conversation_path="logs/conversation",
                browser_context=context,
                initial_actions=initial_actions,
                max_actions_per_step=4,
                controller=controller,
            )
            
            # Run the agent to navigate to the profile
            history = await agent.run(max_steps=5)
            
            # Wait for profile to load
            print(f"Waiting {self.page_load_delay} seconds for profile to load...")
            await asyncio.sleep(self.page_load_delay)
            
            # Create new actions to click on followers link
            follow_actions = [
                {"click": {"selector": "a[href*='followers']"}},
            ]
            
            # Create agent to click on followers link
            followers_agent = Agent(
                task=f"Click on {self.target_username}'s followers link",
                llm=ChatOpenAI(model="gpt-4o"),
                save_conversation_path="logs/conversation",
                browser_context=context,
                initial_actions=follow_actions,
                max_actions_per_step=2,
                controller=controller,
            )
            
            # Run the agent to click on followers link
            followers_history = await followers_agent.run(max_steps=3)
            
            # Wait for followers page to load
            print(f"Waiting {self.page_load_delay} seconds for followers page to load...")
            await asyncio.sleep(self.page_load_delay)
            
            # Verify we're on the followers page
            current_url = await browser.current_url()
            if f"/{self.target_username}/followers" in current_url:
                print(f"Successfully navigated to {self.target_username}'s followers page")
                return True
            else:
                print(f"Failed to navigate to followers page. Current URL: {current_url}")
                return False
                
        except Exception as e:
            print(f"Error navigating to followers page: {e}")
            return False

    async def _process_followers_page(self, browser, context) -> Tuple[int, bool]:
        """
        Process the current followers page by finding and clicking follow buttons
        
        Returns:
            Tuple[int, bool]: (Number of follows completed, Whether more follows are available)
        """
        try:
            # Create agent to find and click follow buttons
            controller = Controller()
            
            # Define the task for finding follow buttons
            follow_task = """
            Find all "Follow" buttons on the current page (white text on black button).
            Ignore buttons that say "Following" or "Pending".
            Click on each "Follow" button one by one.
            Wait 2-3 seconds after each click.
            """
            
            # Create agent to find and click follow buttons
            follow_agent = Agent(
                task=follow_task,
                llm=ChatOpenAI(model="gpt-4o"),
                save_conversation_path="logs/conversation",
                browser_context=context,
                max_actions_per_step=4,
                controller=controller,
            )
            
            # Run the agent to find and click follow buttons
            follows_this_page = 0
            max_follows_this_page = min(self.max_follows_per_page, self.follow_goal - self.follows_completed)
            
            for _ in range(max_follows_this_page):
                # Check if we've reached our follow goal
                if self.follows_completed >= self.follow_goal:
                    return follows_this_page, False
                
                # Run the agent to find and click a follow button
                follow_history = await follow_agent.run(max_steps=3)
                
                # Check if the agent was successful
                if follow_history.final_result():
                    follows_this_page += 1
                    self.follows_completed += 1
                    self.results["follows_completed"] += 1
                    self.results["details"].append({
                        "action": "follow",
                        "timestamp": datetime.now().isoformat(),
                        "status": "success"
                    })
                    
                    print(f"Follow {self.follows_completed}/{self.follow_goal} completed")
                    
                    # Random delay between follows
                    delay = random.uniform(self.min_delay_between_follows, self.max_delay_between_follows)
                    print(f"Waiting {delay:.1f} seconds before next follow...")
                    await asyncio.sleep(delay)
                else:
                    # No more follow buttons found on this page
                    break
            
            # Scroll down to load more followers
            scroll_action = [
                {"scroll": {"direction": "down", "distance": 1000}},
            ]
            
            scroll_agent = Agent(
                task="Scroll down to load more followers",
                llm=ChatOpenAI(model="gpt-4o"),
                save_conversation_path="logs/conversation",
                browser_context=context,
                initial_actions=scroll_action,
                max_actions_per_step=2,
                controller=controller,
            )
            
            # Run the agent to scroll down
            scroll_history = await scroll_agent.run(max_steps=2)
            
            # Wait for new followers to load
            print(f"Waiting {self.scroll_delay} seconds for new followers to load...")
            await asyncio.sleep(self.scroll_delay)
            
            # Check if we found any follows on this page
            if follows_this_page > 0:
                # We found follows, so there might be more
                return follows_this_page, True
            else:
                # We didn't find any follows, so we might need to refresh
                return follows_this_page, False
                
        except Exception as e:
            print(f"Error processing followers page: {e}")
            return 0, False

    async def _refresh_page(self, browser, context) -> bool:
        """
        Refresh the followers page
        
        Returns:
            bool: True if refresh was successful, False otherwise
        """
        try:
            # Increment refresh counter
            self.refresh_count += 1
            self.results["refreshes_performed"] += 1
            
            print(f"Refreshing page ({self.refresh_count}/{self.max_refreshes})...")
            
            # Create refresh action
            refresh_action = [
                {"refresh": {}},
            ]
            
            # Create agent to refresh the page
            controller = Controller()
            refresh_agent = Agent(
                task="Refresh the page",
                llm=ChatOpenAI(model="gpt-4o"),
                save_conversation_path="logs/conversation",
                browser_context=context,
                initial_actions=refresh_action,
                max_actions_per_step=2,
                controller=controller,
            )
            
            # Run the agent to refresh the page
            refresh_history = await refresh_agent.run(max_steps=2)
            
            # Wait for page to reload
            print(f"Waiting {self.page_load_delay} seconds for page to reload...")
            await asyncio.sleep(self.page_load_delay)
            
            # Verify we're still on the followers page
            current_url = await browser.current_url()
            if f"/{self.target_username}/followers" in current_url:
                print("Successfully refreshed followers page")
                return True
            else:
                print(f"Failed to stay on followers page after refresh. Current URL: {current_url}")
                return False
                
        except Exception as e:
            print(f"Error refreshing page: {e}")
            return False

    async def run(self) -> Dict[str, Any]:
        """
        Run the X.com follower automation workflow
        
        Returns:
            Dict[str, Any]: Results of the automation run
        """
        self.start_time = datetime.now()
        self.results["status"] = "Running"
        
        print(f"Starting X.com follower automation for @{self.target_username}")
        print(f"Follow goal: {self.follow_goal}")
        print(f"Max refreshes: {self.max_refreshes}")
        
        try:
            # Initialize browser and context
            browser = Browser()
            cookie_manager = get_cookie_manager()
            context = BrowserContext(
                browser=browser, config=cookie_manager.create_browser_context_config()
            )
            
            # Phase 1: Navigate to target user's followers page
            print("\n=== Phase 1: Navigate to Target ===")
            navigation_success = await self._navigate_to_followers_page(browser, context)
            
            if not navigation_success:
                self.results["status"] = "Failed - Navigation Error"
                print("Failed to navigate to followers page. Aborting.")
                await browser.close()
                return self.results
            
            # Phase 2 & 3: Process followers and refresh as needed
            print("\n=== Phase 2: Process Followers ===")
            consecutive_empty_refreshes = 0
            
            while self.follows_completed < self.follow_goal and self.refresh_count < self.max_refreshes:
                # Process the current page
                follows_this_page, more_available = await self._process_followers_page(browser, context)
                
                # Check if we need to refresh
                if not more_available:
                    print("\n=== Phase 3: Refresh for New Followers ===")
                    refresh_success = await self._refresh_page(browser, context)
                    
                    if not refresh_success:
                        self.results["status"] = "Failed - Refresh Error"
                        print("Failed to refresh followers page. Aborting.")
                        break
                    
                    # Track consecutive empty refreshes
                    if follows_this_page == 0:
                        consecutive_empty_refreshes += 1
                    else:
                        consecutive_empty_refreshes = 0
                    
                    # Stop if we've had 3 consecutive empty refreshes
                    if consecutive_empty_refreshes >= 3:
                        self.results["status"] = "Completed - No More Targets"
                        print("No more follow buttons found after 3 consecutive refreshes. Stopping.")
                        break
            
            # Phase 4: Complete and report
            print("\n=== Phase 4: Complete and Report ===")
            
            # Determine final status
            if self.follows_completed >= self.follow_goal:
                self.results["status"] = "Completed - Goal Reached"
            elif self.refresh_count >= self.max_refreshes:
                self.results["status"] = "Completed - Refresh Limit Reached"
            
            # Close browser
            await browser.close()
            
        except Exception as e:
            self.results["status"] = f"Failed - Error: {str(e)}"
            print(f"Error during automation: {e}")
        
        # Calculate time taken
        self.end_time = datetime.now()
        time_taken = self.end_time - self.start_time
        self.results["time_taken"] = str(time_taken)
        
        # Print final report
        print("\n=== Final Report ===")
        print(f"Total new follows completed: {self.follows_completed}")
        print(f"Total page refreshes: {self.refresh_count}")
        print(f"Time taken: {time_taken}")
        print(f"Final status: {self.results['status']}")
        
        return self.results


async def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(description="X.com Follower Automation")
    parser.add_argument(
        "--target", 
        type=str, 
        required=True,
        help="Target username (the account whose followers you want to follow)"
    )
    parser.add_argument(
        "--goal", 
        type=int, 
        default=10,
        help="Follow goal (how many new follows to complete)"
    )
    parser.add_argument(
        "--max-refreshes", 
        type=int, 
        default=10,
        help="Maximum number of page refreshes before stopping"
    )
    parser.add_argument(
        "--save-results", 
        action="store_true",
        help="Save results to a JSON file"
    )
    
    args = parser.parse_args()
    
    # Create and run the automation
    automation = XFollowerAutomation(
        target_username=args.target,
        follow_goal=args.goal,
        max_refreshes=args.max_refreshes
    )
    
    results = await automation.run()
    
    # Save results if requested
    if args.save_results:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"results_{args.target}_{timestamp}.json"
        
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"Results saved to {results_file}")


if __name__ == "__main__":
    asyncio.run(main())

