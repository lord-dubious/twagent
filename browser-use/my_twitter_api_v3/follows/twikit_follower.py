#!/usr/bin/env python3
"""
Twitter Follower Module using Twikit
Fetches followers from target accounts and follows them with rate limiting
"""

import asyncio
import json
import os
import time
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass, field

import twikit
from ..utils.cookie_manager import get_cookie_manager, load_cookies


@dataclass
class RateLimitTracker:
    """Tracks rate limits for following operations"""
    follows_today: int = 0
    follows_this_minute: int = 0
    last_follow_time: Optional[datetime] = None
    minute_reset_time: Optional[datetime] = None
    day_reset_time: Optional[datetime] = None


@dataclass
class FollowTarget:
    """Target account to get followers from"""
    handle: str
    max_followers: int = 100
    min_followers_count: int = 10  # Minimum followers a user should have to be considered
    max_following_count: int = 5000  # Maximum following count to avoid spam accounts
    verified_only: bool = False
    followed_users: Set[str] = field(default_factory=set)
    
    def __post_init__(self):
        # Ensure handle doesn't have @ prefix for internal use
        self.handle = self.handle.lstrip('@')


class TwikitFollower:
    """Twitter follower system using Twikit library"""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the follower with configuration"""
        self.config = self._load_config(config_path)
        self.rate_tracker = RateLimitTracker()
        self._setup_rate_limits()
        self.client = None
        self.targets = []
        self.followed_users = set()
        self.users_to_follow = []
        self.target_file = self.config.get("following", {}).get("targets_file", "./target_accounts.json")
        
        # Make target file path absolute if relative
        if not os.path.isabs(self.target_file):
            current_dir = os.path.dirname(os.path.abspath(__file__))
            self.target_file = os.path.join(current_dir, "../../../../", self.target_file)
    
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
    
    async def initialize_client(self):
        """Initialize the Twikit client with cookies"""
        if self.client is not None:
            return
        
        self.client = twikit.Client()
        
        # Load cookies from the cookie file
        cookie_manager = get_cookie_manager()
        cookies = cookie_manager.load_cookies()
        
        # Convert cookies to the format expected by twikit
        cookie_dict = {}
        for cookie in cookies:
            cookie_dict[cookie['name']] = cookie['value']
        
        # Set cookies in the twikit client
        for name, value in cookie_dict.items():
            self.client.http.cookies.set(name, value, domain='.x.com')
        
        print("Twikit client initialized with cookies")
    
    def load_targets(self) -> List[FollowTarget]:
        """Load target accounts from JSON file"""
        try:
            with open(self.target_file, 'r') as f:
                data = json.load(f)
                targets = []
                for target_data in data.get("targets", []):
                    targets.append(FollowTarget(
                        handle=target_data["handle"],
                        max_followers=target_data.get("max_followers", 100),
                        min_followers_count=target_data.get("min_followers_count", 10),
                        max_following_count=target_data.get("max_following_count", 5000),
                        verified_only=target_data.get("verified_only", False)
                    ))
                self.targets = targets
                return targets
        except (FileNotFoundError, json.JSONDecodeError) as e:
            # Create a default targets file if it doesn't exist
            if isinstance(e, FileNotFoundError):
                default_targets = {
                    "targets": [
                        {
                            "handle": "elonmusk",
                            "max_followers": 100,
                            "min_followers_count": 10,
                            "max_following_count": 5000,
                            "verified_only": False
                        }
                    ]
                }
                os.makedirs(os.path.dirname(self.target_file), exist_ok=True)
                with open(self.target_file, 'w') as f:
                    json.dump(default_targets, f, indent=2)
                self.targets = [FollowTarget(
                    handle="elonmusk",
                    max_followers=100,
                    min_followers_count=10,
                    max_following_count=5000,
                    verified_only=False
                )]
                print(f"Created default targets file at {self.target_file}")
                return self.targets
            raise Exception(f"Error loading targets from {self.target_file}: {e}")
    
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
        """Wait the configured delay between follows with some randomization"""
        if self.rate_tracker.last_follow_time:
            elapsed = (datetime.now() - self.rate_tracker.last_follow_time).total_seconds()
            base_delay = self.delay_between_follows
            # Add some randomization to avoid detection
            jitter = random.uniform(0, 2)
            total_delay = base_delay + jitter
            
            if elapsed < total_delay:
                wait_time = total_delay - elapsed
                print(f"Waiting {wait_time:.1f} seconds before next follow...")
                time.sleep(wait_time)
    
    async def get_followers_from_target(self, target: FollowTarget) -> List[Dict[str, Any]]:
        """Get followers from a target account"""
        try:
            print(f"Getting followers for @{target.handle}...")
            
            # Get user by screen name
            user = await self.client.get_user_by_screen_name(target.handle)
            
            # Get followers
            followers_result = await user.get_followers(count=target.max_followers)
            followers = []
            
            for follower in followers_result:
                # Skip users we've already followed
                if follower.id in self.followed_users or follower.id in target.followed_users:
                    continue
                
                # Apply filters
                if target.verified_only and not follower.verified and not follower.is_blue_verified:
                    continue
                
                if follower.followers_count < target.min_followers_count:
                    continue
                
                if follower.following_count > target.max_following_count:
                    continue
                
                # Skip protected accounts
                if follower.protected:
                    continue
                
                followers.append({
                    "id": follower.id,
                    "screen_name": follower.screen_name,
                    "name": follower.name,
                    "followers_count": follower.followers_count,
                    "following_count": follower.following_count,
                    "verified": follower.verified or follower.is_blue_verified,
                    "source_account": target.handle
                })
            
            print(f"Found {len(followers)} eligible followers from @{target.handle}")
            return followers
            
        except Exception as e:
            print(f"Error getting followers for @{target.handle}: {e}")
            return []
    
    async def follow_user_by_id(self, user_id: str, screen_name: str) -> bool:
        """Follow a user by their ID using twikit"""
        try:
            # Get user by ID
            user = await self.client.get_user_by_id(user_id)
            
            # Follow the user
            response = await user.follow()
            
            # Check if follow was successful
            if response.status_code == 200:
                return True
            else:
                print(f"Failed to follow @{screen_name} (ID: {user_id}). Status code: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"Error following @{screen_name} (ID: {user_id}): {e}")
            return False
    
    async def follow_user(self, user_data: Dict[str, Any]) -> bool:
        """Follow a single user with rate limiting"""
        if not self._check_rate_limits():
            print("Rate limits exceeded. Cannot follow user at this time.")
            return False
        
        self._wait_between_follows()
        
        user_id = user_data["id"]
        screen_name = user_data["screen_name"]
        
        success = await self.follow_user_by_id(user_id, screen_name)
        
        if success:
            self.rate_tracker.follows_today += 1
            self.rate_tracker.follows_this_minute += 1
            self.rate_tracker.last_follow_time = datetime.now()
            self.followed_users.add(user_id)
            
            # Add to the target's followed users set
            for target in self.targets:
                if target.handle == user_data["source_account"]:
                    target.followed_users.add(user_id)
                    break
            
            print(f"✓ Successfully followed @{screen_name} (from @{user_data['source_account']})")
        else:
            print(f"✗ Failed to follow @{screen_name}")
        
        return success
    
    async def collect_users_to_follow(self):
        """Collect users to follow from all target accounts"""
        if not self.targets:
            self.load_targets()
        
        await self.initialize_client()
        
        all_users = []
        for target in self.targets:
            users = await self.get_followers_from_target(target)
            all_users.extend(users)
        
        # Shuffle the list to randomize the order
        random.shuffle(all_users)
        
        self.users_to_follow = all_users
        print(f"Collected {len(all_users)} users to follow from {len(self.targets)} target accounts")
        return all_users
    
    async def follow_collected_users(self, max_users: Optional[int] = None):
        """Follow users that have been collected"""
        if not self.users_to_follow:
            print("No users to follow. Run collect_users_to_follow() first.")
            return {"followed": 0, "failed": 0, "skipped": 0}
        
        users_to_process = self.users_to_follow
        if max_users is not None:
            users_to_process = users_to_process[:max_users]
        
        followed = 0
        failed = 0
        
        for user in users_to_process:
            if user["id"] in self.followed_users:
                continue
                
            success = await self.follow_user(user)
            
            if success:
                followed += 1
            else:
                failed += 1
                
            # Remove from the list regardless of success to avoid retrying
            if user in self.users_to_follow:
                self.users_to_follow.remove(user)
        
        return {
            "followed": followed,
            "failed": failed,
            "skipped": len(users_to_process) - followed - failed
        }
    
    async def run_full_workflow(self, max_users: Optional[int] = None):
        """Run the full workflow: collect users and follow them"""
        await self.initialize_client()
        await self.collect_users_to_follow()
        results = await self.follow_collected_users(max_users)
        
        print("\n=== Follow Workflow Complete ===")
        print(f"Total followed: {results['followed']}")
        print(f"Total failed: {results['failed']}")
        print(f"Total skipped: {results['skipped']}")
        print(f"Remaining users to follow: {len(self.users_to_follow)}")
        
        return results
    
    def get_follow_status(self) -> Dict[str, Any]:
        """Get the current following status"""
        return {
            "rate_limits": {
                "follows_today": self.rate_tracker.follows_today,
                "follows_this_minute": self.rate_tracker.follows_this_minute,
                "follows_per_day": self.follows_per_day,
                "follows_per_minute": self.follows_per_minute,
                "delay_between_follows": self.delay_between_follows
            },
            "targets": [
                {
                    "handle": target.handle,
                    "max_followers": target.max_followers,
                    "min_followers_count": target.min_followers_count,
                    "max_following_count": target.max_following_count,
                    "verified_only": target.verified_only,
                    "followed_users_count": len(target.followed_users)
                }
                for target in self.targets
            ],
            "users_to_follow_count": len(self.users_to_follow),
            "total_followed_count": len(self.followed_users)
        }


# Singleton instance for easy access
_twikit_follower_instance = None

def get_twikit_follower() -> TwikitFollower:
    """Get the global TwikitFollower instance"""
    global _twikit_follower_instance
    if _twikit_follower_instance is None:
        _twikit_follower_instance = TwikitFollower()
    return _twikit_follower_instance

async def follow_user(user_data: Dict[str, Any]) -> bool:
    """Convenience function to follow a single user"""
    follower = get_twikit_follower()
    await follower.initialize_client()
    return await follower.follow_user(user_data)

async def run_follow_workflow(max_users: Optional[int] = None) -> Dict[str, Any]:
    """Convenience function to run the full follow workflow"""
    follower = get_twikit_follower()
    return await follower.run_full_workflow(max_users)


if __name__ == "__main__":
    import argparse
    
    async def main():
        parser = argparse.ArgumentParser(description="Twitter Follower using Twikit")
        parser.add_argument("--collect", action="store_true", help="Collect users to follow")
        parser.add_argument("--follow", action="store_true", help="Follow collected users")
        parser.add_argument("--max", type=int, help="Maximum number of users to follow")
        parser.add_argument("--status", action="store_true", help="Show current status")
        parser.add_argument("--run", action="store_true", help="Run the full workflow")
        
        args = parser.parse_args()
        
        follower = get_twikit_follower()
        
        if args.status or (not args.collect and not args.follow and not args.run):
            follower.load_targets()
            status = follower.get_follow_status()
            print("\n=== Current Following Status ===")
            print(json.dumps(status, indent=2))
            return
        
        await follower.initialize_client()
        
        if args.collect:
            await follower.collect_users_to_follow()
        
        if args.follow:
            results = await follower.follow_collected_users(args.max)
            print("\n=== Follow Results ===")
            print(json.dumps(results, indent=2))
        
        if args.run:
            await follower.run_full_workflow(args.max)
    
    asyncio.run(main())

