#!/usr/bin/env python3
"""
Twikit Follow Workflow
Orchestrates following operations using Twikit to get followers from target accounts
"""

import argparse
import asyncio
import json
import os
import sys
from datetime import datetime

from browser_use.my_twitter_api_v3.follows.twikit_follower import (
    get_twikit_follower,
    run_follow_workflow
)


async def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(description="Twitter Follower using Twikit")
    parser.add_argument(
        "--collect",
        action="store_true",
        help="Collect users to follow without following them"
    )
    parser.add_argument(
        "--follow",
        action="store_true",
        help="Follow users that have been collected"
    )
    parser.add_argument(
        "--max",
        type=int,
        help="Maximum number of users to follow"
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Show current status"
    )
    parser.add_argument(
        "--run",
        action="store_true",
        help="Run the full workflow (collect and follow)"
    )
    parser.add_argument(
        "--target",
        type=str,
        help="Add a new target account to get followers from"
    )
    parser.add_argument(
        "--list-targets",
        action="store_true",
        help="List all target accounts"
    )
    parser.add_argument(
        "--remove-target",
        type=str,
        help="Remove a target account by handle"
    )
    
    args = parser.parse_args()
    
    follower = get_twikit_follower()
    
    # Handle target management
    if args.target:
        await add_target(args.target)
        return
    
    if args.list_targets:
        list_targets()
        return
    
    if args.remove_target:
        remove_target(args.remove_target)
        return
    
    # Handle status display
    if args.status or (not args.collect and not args.follow and not args.run):
        follower.load_targets()
        status = follower.get_follow_status()
        print("\n=== Current Following Status ===")
        print(json.dumps(status, indent=2))
        return
    
    # Initialize the client
    try:
        await follower.initialize_client()
    except Exception as e:
        print(f"Error initializing Twikit client: {e}")
        print("Make sure your cookies.json file is properly configured.")
        return
    
    # Handle collection
    if args.collect:
        try:
            users = await follower.collect_users_to_follow()
            print(f"Collected {len(users)} users to follow")
        except Exception as e:
            print(f"Error collecting users: {e}")
            return
    
    # Handle following
    if args.follow:
        try:
            results = await follower.follow_collected_users(args.max)
            print("\n=== Follow Results ===")
            print(json.dumps(results, indent=2))
        except Exception as e:
            print(f"Error following users: {e}")
            return
    
    # Handle full workflow
    if args.run:
        try:
            await run_follow_workflow(args.max)
        except Exception as e:
            print(f"Error running workflow: {e}")
            return


async def add_target(handle: str):
    """Add a new target account to the targets file"""
    handle = handle.lstrip('@')
    
    follower = get_twikit_follower()
    target_file = follower.target_file
    
    try:
        with open(target_file, 'r') as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        data = {"targets": []}
    
    # Check if target already exists
    for target in data["targets"]:
        if target["handle"].lower() == handle.lower():
            print(f"Target @{handle} already exists in the targets file.")
            return
    
    # Add new target
    new_target = {
        "handle": handle,
        "max_followers": 100,
        "min_followers_count": 10,
        "max_following_count": 5000,
        "verified_only": False
    }
    
    data["targets"].append(new_target)
    
    # Update metadata
    if "metadata" not in data:
        data["metadata"] = {}
    
    data["metadata"]["last_updated"] = datetime.now().isoformat()
    
    # Save the updated file
    os.makedirs(os.path.dirname(target_file), exist_ok=True)
    with open(target_file, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"Added @{handle} to target accounts.")
    
    # Verify the target exists on Twitter
    try:
        await follower.initialize_client()
        user = await follower.client.get_user_by_screen_name(handle)
        print(f"Verified @{handle} exists on Twitter with {user.followers_count} followers.")
    except Exception as e:
        print(f"Warning: Could not verify @{handle} on Twitter: {e}")


def list_targets():
    """List all target accounts"""
    follower = get_twikit_follower()
    targets = follower.load_targets()
    
    print("\n=== Target Accounts ===")
    for i, target in enumerate(targets, 1):
        print(f"{i}. @{target.handle} (max: {target.max_followers}, verified only: {target.verified_only})")
    
    print(f"\nTotal: {len(targets)} target accounts")


def remove_target(handle: str):
    """Remove a target account from the targets file"""
    handle = handle.lstrip('@')
    
    follower = get_twikit_follower()
    target_file = follower.target_file
    
    try:
        with open(target_file, 'r') as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        print("Target file not found or invalid.")
        return
    
    # Find and remove the target
    found = False
    for i, target in enumerate(data["targets"]):
        if target["handle"].lower() == handle.lower():
            del data["targets"][i]
            found = True
            break
    
    if not found:
        print(f"Target @{handle} not found in the targets file.")
        return
    
    # Update metadata
    if "metadata" not in data:
        data["metadata"] = {}
    
    from datetime import datetime
    data["metadata"]["last_updated"] = datetime.now().isoformat()
    
    # Save the updated file
    with open(target_file, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"Removed @{handle} from target accounts.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
