#!/usr/bin/env python3
"""
Twitter API Example

This script demonstrates the usage of the refactored Twitter API module.
"""

import asyncio
import argparse
from typing import List, Optional

from browser_use.twitter_api import (
    get_tweet,
    create_post,
    reply_to_post,
    follow_user,
    block_user,
    create_list,
    add_members_to_list,
    get_list_posts
)


async def get_tweet_example(tweet_url: str):
    """Example of getting a tweet"""
    print(f"Getting tweet from {tweet_url}...")
    tweet = await get_tweet(tweet_url)
    
    if tweet:
        print("\nTweet retrieved successfully:")
        print(f"Handle: @{tweet.handle}")
        print(f"Text: {tweet.text}")
        print(f"Likes: {tweet.likes}")
        print(f"Retweets: {tweet.retweets}")
        print(f"Replies: {tweet.replies}")
        print(f"Bookmarks: {tweet.bookmarks}")
        print(f"View count: {tweet.viewcount}")
        print(f"Date/time: {tweet.datetime}")
    else:
        print("Failed to retrieve tweet.")


async def create_post_example(post_text: str, media_path: Optional[str] = None):
    """Example of creating a post"""
    print(f"Creating post: {post_text}")
    if media_path:
        print(f"With media: {media_path}")
    
    success = await create_post(post_text, media_path)
    
    if success:
        print("Post created successfully!")
    else:
        print("Failed to create post.")


async def reply_to_post_example(post_url: str, reply_text: str, media_path: Optional[str] = None):
    """Example of replying to a post"""
    print(f"Replying to {post_url}")
    print(f"Reply text: {reply_text}")
    if media_path:
        print(f"With media: {media_path}")
    
    success = await reply_to_post(post_url, reply_text, media_path)
    
    if success:
        print("Reply created successfully!")
    else:
        print("Failed to create reply.")


async def follow_user_example(username: str):
    """Example of following a user"""
    print(f"Following user @{username}...")
    
    success = await follow_user(username)
    
    if success:
        print(f"Successfully followed @{username}!")
    else:
        print(f"Failed to follow @{username}.")


async def block_user_example(username: str):
    """Example of blocking a user"""
    print(f"Blocking user @{username}...")
    
    success = await block_user(username)
    
    if success:
        print(f"Successfully blocked @{username}!")
    else:
        print(f"Failed to block @{username}.")


async def create_list_example(list_name: str, description: str):
    """Example of creating a list"""
    print(f"Creating list '{list_name}'...")
    print(f"Description: {description}")
    
    success = await create_list(list_name, description)
    
    if success:
        print(f"Successfully created list '{list_name}'!")
    else:
        print(f"Failed to create list '{list_name}'.")


async def add_members_to_list_example(list_name: str, usernames: List[str]):
    """Example of adding members to a list"""
    print(f"Adding members to list '{list_name}'...")
    print(f"Members: {', '.join(['@' + username for username in usernames])}")
    
    success = await add_members_to_list(list_name, usernames)
    
    if success:
        print(f"Successfully added members to list '{list_name}'!")
    else:
        print(f"Failed to add members to list '{list_name}'.")


async def get_list_posts_example(list_name: str):
    """Example of getting posts from a list"""
    print(f"Getting posts from list '{list_name}'...")
    
    success = await get_list_posts(list_name)
    
    if success:
        print(f"Successfully retrieved posts from list '{list_name}'!")
    else:
        print(f"Failed to retrieve posts from list '{list_name}'.")


async def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Twitter API Example")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Get tweet command
    get_tweet_parser = subparsers.add_parser("get-tweet", help="Get a tweet")
    get_tweet_parser.add_argument("tweet_url", help="URL of the tweet")
    
    # Create post command
    create_post_parser = subparsers.add_parser("create-post", help="Create a post")
    create_post_parser.add_argument("post_text", help="Text of the post")
    create_post_parser.add_argument("--media", help="Path to media file")
    
    # Reply to post command
    reply_parser = subparsers.add_parser("reply", help="Reply to a post")
    reply_parser.add_argument("post_url", help="URL of the post to reply to")
    reply_parser.add_argument("reply_text", help="Text of the reply")
    reply_parser.add_argument("--media", help="Path to media file")
    
    # Follow user command
    follow_parser = subparsers.add_parser("follow", help="Follow a user")
    follow_parser.add_argument("username", help="Username of the user to follow")
    
    # Block user command
    block_parser = subparsers.add_parser("block", help="Block a user")
    block_parser.add_argument("username", help="Username of the user to block")
    
    # Create list command
    create_list_parser = subparsers.add_parser("create-list", help="Create a list")
    create_list_parser.add_argument("list_name", help="Name of the list")
    create_list_parser.add_argument("description", help="Description of the list")
    
    # Add members to list command
    add_members_parser = subparsers.add_parser("add-members", help="Add members to a list")
    add_members_parser.add_argument("list_name", help="Name of the list")
    add_members_parser.add_argument("usernames", nargs="+", help="Usernames to add to the list")
    
    # Get list posts command
    get_list_posts_parser = subparsers.add_parser("get-list-posts", help="Get posts from a list")
    get_list_posts_parser.add_argument("list_name", help="Name of the list")
    
    args = parser.parse_args()
    
    if args.command == "get-tweet":
        await get_tweet_example(args.tweet_url)
    elif args.command == "create-post":
        await create_post_example(args.post_text, args.media)
    elif args.command == "reply":
        await reply_to_post_example(args.post_url, args.reply_text, args.media)
    elif args.command == "follow":
        await follow_user_example(args.username)
    elif args.command == "block":
        await block_user_example(args.username)
    elif args.command == "create-list":
        await create_list_example(args.list_name, args.description)
    elif args.command == "add-members":
        await add_members_to_list_example(args.list_name, args.usernames)
    elif args.command == "get-list-posts":
        await get_list_posts_example(args.list_name)
    else:
        parser.print_help()


if __name__ == "__main__":
    asyncio.run(main())
