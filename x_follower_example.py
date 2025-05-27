#!/usr/bin/env python3
"""
Example script for using the X.com follower automation
"""

import asyncio
import argparse
from browser_use.x_follower_automation import XFollowerAutomation


async def main():
    """Example usage of the X.com follower automation"""
    
    parser = argparse.ArgumentParser(description="X.com Follower Automation Example")
    parser.add_argument(
        "--target", 
        type=str, 
        default="elonmusk",
        help="Target username (the account whose followers you want to follow)"
    )
    parser.add_argument(
        "--goal", 
        type=int, 
        default=5,
        help="Follow goal (how many new follows to complete)"
    )
    parser.add_argument(
        "--max-refreshes", 
        type=int, 
        default=3,
        help="Maximum number of page refreshes before stopping"
    )
    
    args = parser.parse_args()
    
    print("=== X.com Follower Automation Example ===")
    print(f"Target: @{args.target}")
    print(f"Follow Goal: {args.goal}")
    print(f"Max Refreshes: {args.max_refreshes}")
    print("=" * 40)
    
    # Create the automation instance
    automation = XFollowerAutomation(
        target_username=args.target,
        follow_goal=args.goal,
        max_refreshes=args.max_refreshes
    )
    
    # Run the automation
    results = await automation.run()
    
    # Print results
    print("\n=== Final Results ===")
    print(f"Status: {results['status']}")
    print(f"Follows Completed: {results['follows_completed']}")
    print(f"Refreshes Performed: {results['refreshes_performed']}")
    print(f"Time Taken: {results['time_taken']}")


if __name__ == "__main__":
    asyncio.run(main())

