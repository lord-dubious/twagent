#!/usr/bin/env python3
"""
Twitter Follower Automation

This script automates the process of following users from a target account's followers list.
It uses the browser-use package to control the browser and interact with Twitter.
"""

import asyncio
import argparse
import time
import random
from typing import Dict, List, Any, Optional, Union
from datetime import datetime

from browser_use import Agent, Browser, Controller
from browser_use.browser.context import BrowserContext
from browser_use.agent.views import AgentHistoryList
from langchain_openai import ChatOpenAI

from twitter_api import TwitterBrowserSession, get_twitter_config


class FollowerAutomation:
    """Automates following users from a target account's followers list"""
    
    def __init__(
        self,
        target_username: str,
        follow_goal: int,
        max_refreshes: int = 10,
        delay_between_follows: float = 2.5,
        delay_after_error: float = 10.0,
        batch_size: int = 20
    ):
        """
        Initialize the follower automation
        
        Args:
            target_username: Username of the target account
            follow_goal: Number of users to follow
            max_refreshes: Maximum number of page refreshes
            delay_between_follows: Delay between follow actions in seconds
            delay_after_error: Delay after an error in seconds
            batch_size: Number of follows per batch before scrolling
        """
        self.target_username = target_username.lstrip('@')
        self.follow_goal = follow_goal
        self.max_refreshes = max_refreshes
        self.delay_between_follows = delay_between_follows
        self.delay_after_error = delay_after_error
        self.batch_size = batch_size
        
        self.config = get_twitter_config()
        self.follows_completed = 0
        self.refreshes_done = 0
        self.start_time = None
        self.end_time = None
        
        # Results tracking
        self.results = {
            "target_username": self.target_username,
            "follow_goal": self.follow_goal,
            "follows_completed": 0,
            "refreshes_done": 0,
            "time_taken": None,
            "status": None,
            "errors": []
        }
    
    async def run(self) -> Dict[str, Any]:
        """
        Run the follower automation
        
        Returns:
            Dictionary with results
        """
        self.start_time = datetime.now()
        print(f"Starting follower automation for @{self.target_username}")
        print(f"Goal: Follow {self.follow_goal} users")
        print(f"Max refreshes: {self.max_refreshes}")
        
        browser = Browser()
        
        try:
            # Phase 1: Navigate to target's followers page
            followers_url = f"https://x.com/{self.target_username}/followers"
            
            async with TwitterBrowserSession(self.config, browser=browser) as session:
                # Initial navigation to followers page
                agent = session.create_agent(
                    task=f"Navigate to {followers_url} and wait for the page to load completely",
                    initial_actions=[{"open_tab": {"url": followers_url}}],
                    max_steps=3
                )
                
                history = await agent.run()
                if not history.is_done():
                    self.results["status"] = "Failed to navigate to followers page"
                    self.results["errors"].append("Navigation to followers page failed")
                    return self.results
                
                print(f"Successfully navigated to {followers_url}")
                
                # Phase 2: Process followers
                consecutive_empty_refreshes = 0
                
                while (self.follows_completed < self.follow_goal and 
                       self.refreshes_done < self.max_refreshes and
                       consecutive_empty_refreshes < 3):
                    
                    # Find and click follow buttons
                    follows_in_batch = await self._process_current_followers(session)
                    
                    if follows_in_batch > 0:
                        consecutive_empty_refreshes = 0
                        print(f"Followed {follows_in_batch} users in this batch")
                        
                        # Check if we've reached our goal
                        if self.follows_completed >= self.follow_goal:
                            self.results["status"] = "Goal Reached"
                            break
                        
                        # Scroll down to load more followers
                        scroll_agent = session.create_agent(
                            task="Scroll down to the bottom of the page to load more followers",
                            initial_actions=[{"scroll_down": {"amount": 1000}}],
                            max_steps=2
                        )
                        await scroll_agent.run()
                        
                        # Wait for new content to load
                        await asyncio.sleep(4)
                    else:
                        # No follow buttons found, refresh the page
                        print("No new follow buttons found, refreshing page...")
                        self.refreshes_done += 1
                        consecutive_empty_refreshes += 1
                        
                        refresh_agent = session.create_agent(
                            task="Refresh the page and wait for it to load completely",
                            initial_actions=[{"refresh_page": {}}],
                            max_steps=2
                        )
                        await refresh_agent.run()
                        
                        # Wait for page to reload
                        await asyncio.sleep(5)
                        
                        if self.refreshes_done >= self.max_refreshes:
                            self.results["status"] = "Refresh Limit Reached"
                            break
                
                # Set final status if not already set
                if not self.results["status"]:
                    if consecutive_empty_refreshes >= 3:
                        self.results["status"] = "No More Targets"
                    elif self.follows_completed >= self.follow_goal:
                        self.results["status"] = "Goal Reached"
                    else:
                        self.results["status"] = "Completed"
        
        except Exception as e:
            print(f"Error during automation: {e}")
            self.results["status"] = "Error"
            self.results["errors"].append(str(e))
        
        finally:
            # Clean up
            await browser.close()
            
            # Calculate time taken
            self.end_time = datetime.now()
            time_taken = self.end_time - self.start_time
            self.results["time_taken"] = str(time_taken)
            
            # Update final results
            self.results["follows_completed"] = self.follows_completed
            self.results["refreshes_done"] = self.refreshes_done
            
            # Print summary
            print("\nAutomation completed!")
            print(f"Total follows: {self.follows_completed}")
            print(f"Total refreshes: {self.refreshes_done}")
            print(f"Time taken: {time_taken}")
            print(f"Final status: {self.results['status']}")
            
            return self.results
    
    async def _process_current_followers(self, session: TwitterBrowserSession) -> int:
        """
        Process the currently visible followers
        
        Args:
            session: TwitterBrowserSession instance
            
        Returns:
            Number of users followed in this batch
        """
        # Create an agent to find and click follow buttons
        agent = session.create_agent(
            task=f"""
            Find all "Follow" buttons on the current page (white text on black button).
            Ignore buttons that say "Following" or "Pending".
            Click on up to {min(self.batch_size, self.follow_goal - self.follows_completed)} "Follow" buttons.
            Wait 2-3 seconds between each click.
            Report how many buttons you clicked.
            """,
            initial_actions=[],
            max_steps=self.batch_size * 2  # Allow enough steps for each follow action
        )
        
        history = await agent.run()
        
        # Extract the number of follows from the result
        result = history.final_result()
        follows_in_batch = 0
        
        try:
            # Try to parse the result to get the number of follows
            if result and isinstance(result, str):
                # Look for numbers in the result
                import re
                numbers = re.findall(r'\d+', result)
                if numbers:
                    follows_in_batch = int(numbers[0])
                else:
                    # If no numbers found, check for keywords
                    if "no" in result.lower() or "zero" in result.lower():
                        follows_in_batch = 0
                    elif "one" in result.lower():
                        follows_in_batch = 1
                    elif "two" in result.lower():
                        follows_in_batch = 2
                    elif "three" in result.lower():
                        follows_in_batch = 3
                    else:
                        # Default to counting "clicked" occurrences
                        follows_in_batch = result.lower().count("clicked")
        except Exception as e:
            print(f"Error parsing follow result: {e}")
            follows_in_batch = 0
        
        # Update the total follows
        self.follows_completed += follows_in_batch
        return follows_in_batch


async def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Twitter Follower Automation")
    parser.add_argument("username", help="Target username whose followers you want to follow")
    parser.add_argument("--goal", type=int, default=10, help="Number of users to follow (default: 10)")
    parser.add_argument("--max-refreshes", type=int, default=10, help="Maximum number of page refreshes (default: 10)")
    parser.add_argument("--delay", type=float, default=2.5, help="Delay between follows in seconds (default: 2.5)")
    parser.add_argument("--batch-size", type=int, default=20, help="Number of follows per batch (default: 20)")
    
    args = parser.parse_args()
    
    automation = FollowerAutomation(
        target_username=args.username,
        follow_goal=args.goal,
        max_refreshes=args.max_refreshes,
        delay_between_follows=args.delay,
        batch_size=args.batch_size
    )
    
    results = await automation.run()
    
    # Save results to file
    import json
    from pathlib import Path
    
    results_dir = Path("results")
    results_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = results_dir / f"follower_automation_{args.username}_{timestamp}.json"
    
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"Results saved to {results_file}")


if __name__ == "__main__":
    asyncio.run(main())

