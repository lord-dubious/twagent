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
from browser_use.my_twitter_api_v3.media_manager import MediaManager


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
        help="Path to media file to include"
    )
    parser.add_argument(
        "--media-dir", 
        type=str, 
        default="media",
        help="Path to media directory for random media selection"
    )
    parser.add_argument(
        "--random-media", 
        action="store_true",
        help="Use random media from the media directory"
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
    
    # Create media manager
    media_manager = MediaManager(media_dir=args.media_dir, llm_model=args.model)
    
    # Get persona name
    persona_name = generator.persona_manager.persona_context.agent_name
    
    print(f"=== Persona-based Tweet Generator for {persona_name} ===")
    print(f"Action: {args.action}")
    
    # Handle random media selection
    media_path = args.media
    media_description = None
    
    if args.random_media and not media_path:
        # Get persona context for media selection
        persona_context = None
        if generator.persona_manager.persona_context:
            persona_context = {
                "agent_name": generator.persona_manager.persona_context.agent_name,
                "system": generator.persona_manager.persona_context.system,
                "topics": generator.persona_manager.persona_context.topics,
                "adjectives": generator.persona_manager.persona_context.adjectives
            }
        
        media_path = media_manager.get_random_media(persona_context=persona_context)
        
        if media_path:
            print(f"Selected random media: {media_path}")
            
            # Generate caption
            media_description = await media_manager.generate_caption(media_path, persona_context=persona_context)
            print(f"Generated caption: {media_description}")
        else:
            print("No suitable media files found. Creating text-only content.")
    
    # Perform action
    if args.action == "post":
        # Generate post - topics and adjectives are automatically selected
        post = await generator.generate_post(
            media_description=media_description
        )
        
        print("\nGenerated Post:")
        print(post)
        print(f"Character count: {len(post)}")
        
        if media_path:
            print(f"Media: {media_path}")
        
    elif args.action == "reply":
        # Check if tweet is provided
        if not args.tweet:
            print("Error: Original tweet is required for reply action.")
            return
        
        # Generate reply
        reply = await generator.generate_reply(
            original_tweet=args.tweet,
            media_description=media_description
        )
        
        print("\nOriginal Tweet:")
        print(args.tweet)
        print("\nGenerated Reply:")
        print(reply)
        print(f"Character count: {len(reply)}")
        
        if media_path:
            print(f"Media: {media_path}")
        
    elif args.action == "quote":
        # Check if tweet is provided
        if not args.tweet:
            print("Error: Original tweet is required for quote action.")
            return
        
        # Generate quote
        quote = await generator.generate_quote_tweet(
            original_tweet=args.tweet,
            media_description=media_description
        )
        
        print("\nOriginal Tweet:")
        print(args.tweet)
        print("\nGenerated Quote:")
        print(quote)
        print(f"Character count: {len(quote)}")
        
        if media_path:
            print(f"Media: {media_path}")
        
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
