#!/usr/bin/env python3
"""
Persona-based Tweet Workflow

This module automates the process of posting tweets with persona integration,
including support for media tweets and persona-based interactions.
"""

import argparse
import asyncio
import json
import os
import random
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Union

from browser_use import Agent, Browser, Controller
from browser_use.browser.context import BrowserContext
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

from .tweet_generator import TweetGenerator
from .media_manager import MediaManager
from .utils.cookie_manager import get_cookie_manager
from .manage_posts.create_post import create_post

load_dotenv()


class PersonaTweetWorkflow:
    """
    Automates the process of posting tweets with persona integration.
    
    This class handles the workflow for posting tweets with persona integration,
    including support for media tweets and persona-based interactions.
    """

    def __init__(self, 
                 persona_file_path: str,
                 llm_model: str = "gpt-4o",
                 media_dir: Optional[str] = None,
                 config_path: Optional[str] = None):
        """
        Initialize the persona tweet workflow.
        
        Args:
            persona_file_path: Path to the persona JSON file
            llm_model: LLM model to use
            media_dir: Path to the media directory (optional)
            config_path: Path to configuration file (optional)
        """
        self.persona_file_path = persona_file_path
        self.llm_model = llm_model
        self.config = self._load_config(config_path)
        
        # Initialize tweet generator
        self.tweet_generator = TweetGenerator(llm_model=llm_model, persona_file_path=persona_file_path)
        
        # Initialize media manager
        self.media_manager = MediaManager(media_dir=media_dir, llm_model=llm_model)
        
        # Initialize tracking variables
        self.posts_created = 0
        self.replies_created = 0
        self.quotes_created = 0
        self.last_post_time = None
    
    def _load_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """Load configuration from config.json"""
        if config_path is None:
            # Search for config.json starting from current file location
            current_dir = os.path.dirname(os.path.abspath(__file__))
            config_path = os.path.join(current_dir, "../../../config.json")
        
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error loading config from {config_path}: {e}")
            return {}
    
    async def create_persona_post(self, media_path: Optional[str] = None, use_random_media: bool = False) -> bool:
        """
        Create a post with persona integration.
        
        Args:
            media_path: Path to media file to include (optional)
            use_random_media: Whether to use a random media file from the media directory
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Get random media if requested
            media_paths = None
            if use_random_media and not media_path:
                # Get persona context for media selection
                persona_context = None
                if self.tweet_generator.persona_manager.persona_context:
                    persona_context = {
                        "agent_name": self.tweet_generator.persona_manager.persona_context.agent_name,
                        "system": self.tweet_generator.persona_manager.persona_context.system,
                        "topics": self.tweet_generator.persona_manager.persona_context.topics,
                        "adjectives": self.tweet_generator.persona_manager.persona_context.adjectives
                    }
                
                # Get random media following Twitter guidelines (max 4 images, 90% chance of single image)
                media_paths = self.media_manager.get_random_media(
                    persona_context=persona_context,
                    max_images=4,
                    single_image_probability=0.9
                )
                
                if not media_paths:
                    print("No suitable media files found. Creating text-only post.")
            elif media_path:
                # Use the provided media path
                media_paths = media_path
            
            # Generate media description if media is provided
            media_description = None
            if media_paths:
                # Handle both single file (string) and multiple files (list)
                if isinstance(media_paths, list):
                    print(f"Using {len(media_paths)} media files: {', '.join(os.path.basename(p) for p in media_paths)}")
                    
                    # Generate caption for the first image to represent the set
                    media_description = await self.media_manager.generate_caption(
                        media_paths[0],
                        persona_context=persona_context if 'persona_context' in locals() else None
                    )
                    
                    media_description = f"A set of {len(media_paths)} images. {media_description}"
                else:
                    print(f"Using media: {media_paths}")
                    
                    # Generate caption
                    media_description = await self.media_manager.generate_caption(
                        media_paths,
                        persona_context=persona_context if 'persona_context' in locals() else None
                    )
                
                print(f"Generated caption: {media_description}")
            
            # Generate post content
            post_content = await self.tweet_generator.generate_post(
                media_description=media_description
            )
            
            # Create post
            # Note: The create_post function needs to be updated to handle multiple media files
            # For now, we'll just use the first file if multiple are provided
            media_path_for_post = media_paths[0] if isinstance(media_paths, list) else media_paths
            success = await create_post(post_content, media_path=media_path_for_post)
            
            if success:
                self.posts_created += 1
                self.last_post_time = datetime.now()
                print(f"Successfully created post: {post_content}")
            else:
                print(f"Failed to create post: {post_content}")
            
            return success
            
        except Exception as e:
            print(f"Error creating persona post: {e}")
            return False
    
    async def create_persona_reply(self, 
                                  tweet_id: str, 
                                  original_tweet: str,
                                  media_path: Optional[str] = None,
                                  use_random_media: bool = False) -> bool:
        """
        Create a reply with persona integration.
        
        Args:
            tweet_id: ID of the tweet to reply to
            original_tweet: Content of the original tweet
            media_path: Path to media file to include (optional)
            use_random_media: Whether to use a random media file from the media directory
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Get random media if requested
            media_paths = None
            if use_random_media and not media_path:
                # Get persona context for media selection
                persona_context = None
                if self.tweet_generator.persona_manager.persona_context:
                    persona_context = {
                        "agent_name": self.tweet_generator.persona_manager.persona_context.agent_name,
                        "system": self.tweet_generator.persona_manager.persona_context.system,
                        "topics": self.tweet_generator.persona_manager.persona_context.topics,
                        "adjectives": self.tweet_generator.persona_manager.persona_context.adjectives
                    }
                
                # Get random media following Twitter guidelines (max 4 images, 90% chance of single image)
                media_paths = self.media_manager.get_random_media(
                    persona_context=persona_context,
                    max_images=4,
                    single_image_probability=0.9
                )
                
                if not media_paths:
                    print("No suitable media files found. Creating text-only reply.")
            elif media_path:
                # Use the provided media path
                media_paths = media_path
            
            # Generate media description if media is provided
            media_description = None
            if media_paths:
                # Handle both single file (string) and multiple files (list)
                if isinstance(media_paths, list):
                    print(f"Using {len(media_paths)} media files: {', '.join(os.path.basename(p) for p in media_paths)}")
                    
                    # Generate caption for the first image to represent the set
                    media_description = await self.media_manager.generate_caption(
                        media_paths[0],
                        persona_context=persona_context if 'persona_context' in locals() else None
                    )
                    
                    media_description = f"A set of {len(media_paths)} images. {media_description}"
                else:
                    print(f"Using media: {media_paths}")
                    
                    # Generate caption
                    media_description = await self.media_manager.generate_caption(
                        media_paths,
                        persona_context=persona_context if 'persona_context' in locals() else None
                    )
                
                print(f"Generated caption: {media_description}")
            
            # Generate reply content
            reply_content = await self.tweet_generator.generate_reply(
                original_tweet=original_tweet,
                media_description=media_description
            )
            
            # Import reply_to_post here to avoid circular imports
            from .manage_posts.reply_to_post import reply_to_post
            
            # Create reply
            # Note: The reply_to_post function needs to be updated to handle multiple media files
            # For now, we'll just use the first file if multiple are provided
            media_path_for_reply = media_paths[0] if isinstance(media_paths, list) else media_paths
            success = await reply_to_post(tweet_id, reply_content, media_path=media_path_for_reply)
            
            if success:
                self.replies_created += 1
                self.last_post_time = datetime.now()
                print(f"Successfully created reply to {tweet_id}: {reply_content}")
            else:
                print(f"Failed to create reply to {tweet_id}: {reply_content}")
            
            return success
            
        except Exception as e:
            print(f"Error creating persona reply: {e}")
            return False
    
    async def run_timeline_monitoring(self, 
                                     interval: int = 3600, 
                                     max_posts: int = 5,
                                     use_random_media: bool = False,
                                     search_terms: Optional[List[str]] = None) -> None:
        """
        Run timeline monitoring to automatically post, reply, and interact.
        
        Args:
            interval: Interval between checks in seconds
            max_posts: Maximum number of posts to create
            use_random_media: Whether to use random media files for posts
            search_terms: List of search terms to monitor (optional)
        """
        try:
            print(f"Starting timeline monitoring with {self.tweet_generator.persona_manager.persona_context.agent_name} persona")
            print(f"Interval: {interval} seconds")
            print(f"Max posts: {max_posts}")
            print(f"Use random media: {use_random_media}")
            
            # Initialize browser
            browser = Browser()
            cookie_manager = get_cookie_manager()
            context = BrowserContext(
                browser=browser, config=cookie_manager.create_browser_context_config()
            )
            
            # Create controller
            controller = Controller()
            
            # Create agent for timeline monitoring
            agent = Agent(
                task="Monitor Twitter timeline and interact with relevant content",
                llm=ChatOpenAI(model=self.llm_model),
                save_conversation_path="logs/conversation",
                browser_context=context,
                max_actions_per_step=4,
                controller=controller,
            )
            
            # Run timeline monitoring loop
            posts_created = 0
            
            while posts_created < max_posts:
                print(f"\n=== Timeline check at {datetime.now()} ===")
                
                # Navigate to Twitter home
                initial_actions = [
                    {"open_tab": {"url": "https://x.com/home"}},
                ]
                
                # Run agent to navigate to home
                history = await agent.run(max_steps=5, initial_actions=initial_actions)
                
                # Wait for timeline to load
                await asyncio.sleep(5)
                
                # Scroll through timeline
                scroll_actions = [
                    {"scroll": {"direction": "down", "distance": 500}},
                ]
                
                # Run agent to scroll
                scroll_history = await agent.run(max_steps=3, initial_actions=scroll_actions)
                
                # Wait for new content to load
                await asyncio.sleep(3)
                
                # Decide whether to post original content
                should_post = random.random() < 0.3  # 30% chance to post
                
                if should_post:
                    print("Creating original post...")
                    success = await self.create_persona_post(use_random_media=use_random_media)
                    if success:
                        posts_created += 1
                
                # Wait for next check
                print(f"Waiting {interval} seconds until next check...")
                await asyncio.sleep(interval)
            
            # Close browser
            await browser.close()
            
            print(f"\n=== Timeline monitoring complete ===")
            print(f"Posts created: {self.posts_created}")
            print(f"Replies created: {self.replies_created}")
            print(f"Quotes created: {self.quotes_created}")
            
        except Exception as e:
            print(f"Error in timeline monitoring: {e}")


async def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(description="Persona-based Tweet Workflow")
    parser.add_argument(
        "--persona", 
        type=str, 
        required=True,
        help="Path to the persona JSON file"
    )
    parser.add_argument(
        "--action", 
        type=str, 
        choices=["post", "monitor"],
        default="post",
        help="Action to perform (post, monitor)"
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
        "--interval", 
        type=int, 
        default=3600,
        help="Interval between checks in seconds (for monitor action)"
    )
    parser.add_argument(
        "--max-posts", 
        type=int, 
        default=5,
        help="Maximum number of posts to create (for monitor action)"
    )
    parser.add_argument(
        "--model", 
        type=str, 
        default="gpt-4o",
        help="LLM model to use"
    )
    
    args = parser.parse_args()
    
    # Create workflow
    workflow = PersonaTweetWorkflow(
        persona_file_path=args.persona,
        llm_model=args.model,
        media_dir=args.media_dir
    )
    
    # Perform action
    if args.action == "post":
        # Create post
        success = await workflow.create_persona_post(
            media_path=args.media,
            use_random_media=args.random_media
        )
        
        if success:
            print("Post created successfully!")
        else:
            print("Failed to create post.")
            
    elif args.action == "monitor":
        # Run timeline monitoring
        await workflow.run_timeline_monitoring(
            interval=args.interval,
            max_posts=args.max_posts,
            use_random_media=args.random_media
        )


if __name__ == "__main__":
    asyncio.run(main())
