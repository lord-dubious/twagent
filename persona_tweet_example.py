#!/usr/bin/env python3
"""
Example script for using the persona-based tweet generator
"""

import asyncio
import argparse
import json
import os
from typing import Optional

from browser_use.my_twitter_api_v3.tweet_generator import TweetGenerator


async def main():
    """Example usage of the persona-based tweet generator"""
    
    parser = argparse.ArgumentParser(description="Persona-based Tweet Generator Example")
    parser.add_argument(
        "--persona", 
        type=str, 
        default="personas/holly_snow.json",
        help="Path to the persona JSON file"
    )
    parser.add_argument(
        "--action", 
        type=str, 
        choices=["post", "reply", "quote", "decide"],
        default="post",
        help="Action to perform (post, reply, quote, decide)"
    )
    parser.add_argument(
        "--tweet", 
        type=str, 
        help="Original tweet to reply to, quote, or decide action on"
    )
    parser.add_argument(
        "--media", 
        type=str, 
        help="Description of media to include"
    )
    parser.add_argument(
        "--model", 
        type=str, 
        default="gpt-4o",
        help="LLM model to use"
    )
    
    args = parser.parse_args()
    
    # Check if persona file exists
    if not os.path.exists(args.persona):
        print(f"Error: Persona file '{args.persona}' not found.")
        return
    
    # Create tweet generator
    generator = TweetGenerator(llm_model=args.model)
    
    # Load persona
    success = generator.load_persona(args.persona)
    if not success:
        print(f"Error: Failed to load persona from '{args.persona}'.")
        return
    
    # Get persona name
    persona_name = generator.persona_manager.persona_context.agent_name
    
    print(f"=== Persona-based Tweet Generator for {persona_name} ===")
    print(f"Action: {args.action}")
    
    # Perform action
    if args.action == "post":
        # Generate post - topics and adjectives are automatically selected
        post = await generator.generate_post(
            media_description=args.media
        )
        
        print("\nGenerated Post:")
        print(post)
        print(f"Character count: {len(post)}")
        
    elif args.action == "reply":
        # Check if tweet is provided
        if not args.tweet:
            print("Error: Original tweet is required for reply action.")
            return
        
        # Generate reply
        reply = await generator.generate_reply(
            original_tweet=args.tweet,
            media_description=args.media
        )
        
        print("\nOriginal Tweet:")
        print(args.tweet)
        print("\nGenerated Reply:")
        print(reply)
        print(f"Character count: {len(reply)}")
        
    elif args.action == "quote":
        # Check if tweet is provided
        if not args.tweet:
            print("Error: Original tweet is required for quote action.")
            return
        
        # Generate quote
        quote = await generator.generate_quote_tweet(
            original_tweet=args.tweet,
            media_description=args.media
        )
        
        print("\nOriginal Tweet:")
        print(args.tweet)
        print("\nGenerated Quote:")
        print(quote)
        print(f"Character count: {len(quote)}")
        
    elif args.action == "decide":
        # Check if tweet is provided
        if not args.tweet:
            print("Error: Tweet is required for decide action.")
            return
        
        # Decide action
        actions = await generator.decide_action(args.tweet)
        
        print("\nTweet to Evaluate:")
        print(args.tweet)
        print("\nDecided Actions:")
        if actions:
            for action in actions:
                print(f"- {action}")
        else:
            print("No actions recommended.")


if __name__ == "__main__":
    asyncio.run(main())
