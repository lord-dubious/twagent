#!/usr/bin/env python3
"""
Simple example of how to use the Twitter following system
"""

import asyncio
from browser_use.my_twitter_api_v3.follows.follow_system import follow_user, get_follower


async def main():
    """Example usage of the Twitter following system"""
    
    # Method 1: Simple single follow
    print("=== Following a single user ===")
    success = await follow_user("elonmusk")
    print(f"Follow result: {'Success' if success else 'Failed'}")
    
    # Method 2: Using the follower instance for more control
    print("\n=== Using follower instance ===")
    follower = get_follower()
    
    # Check current status
    status = follower.get_follow_status()
    print(f"Rate limit status: {status['rate_limits']}")
    
    # Follow multiple users one by one (with rate limiting)
    users_to_follow = ["sama", "pmarca", "garrytan"]
    
    for user in users_to_follow:
        print(f"\nFollowing @{user}...")
        success = await follower.follow_user(user)
        if success:
            print(f"✓ Successfully followed @{user}")
        else:
            print(f"✗ Failed to follow @{user}")
    
    # Show final status
    final_status = follower.get_follow_status()
    print(f"\nFinal rate limit status: {final_status['rate_limits']}")


if __name__ == "__main__":
    asyncio.run(main())
