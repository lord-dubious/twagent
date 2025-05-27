#!/usr/bin/env python3
"""
Tweet Generator for Twitter Automation

This module handles tweet generation for Twitter automation, including:
- LLM-based content creation with persona integration
- Support for media tweets
- Post, reply, and quote tweet generation
"""

import json
import os
import random
import re
from typing import Dict, List, Any, Optional, Tuple, Union
import asyncio

from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage

from .persona_manager import PersonaManager


class TweetGenerator:
    """
    Generates tweets using LLM with persona integration.
    
    This class handles tweet generation for Twitter automation, including
    LLM-based content creation with persona integration, support for media
    tweets, and post, reply, and quote tweet generation.
    """

    def __init__(self, 
                 llm_model: str = "gpt-4o", 
                 persona_file_path: Optional[str] = None,
                 temperature: float = 0.7,
                 max_tokens: int = 1000):
        """
        Initialize the tweet generator.
        
        Args:
            llm_model: LLM model to use
            persona_file_path: Path to the persona JSON file (optional)
            temperature: Temperature for LLM generation
            max_tokens: Maximum tokens for LLM generation
        """
        self.llm = ChatOpenAI(model=llm_model, temperature=temperature, max_tokens=max_tokens)
        self.persona_manager = PersonaManager(persona_file_path)
        self.max_tweet_length = 280  # Twitter's character limit
    
    def load_persona(self, file_path: str) -> bool:
        """
        Load persona data from a JSON file.
        
        Args:
            file_path: Path to the persona JSON file
            
        Returns:
            bool: True if successful, False otherwise
        """
        return self.persona_manager.load_persona(file_path)
    
    async def generate_post(self, 
                           topic: Optional[str] = None, 
                           adjective: Optional[str] = None,
                           media_description: Optional[str] = None) -> str:
        """
        Generate a post tweet.
        
        Args:
            topic: Topic to post about (random if None)
            adjective: Adjective to describe the post (random if None)
            media_description: Description of media to include (optional)
            
        Returns:
            Generated tweet text
        """
        # Generate prompt
        prompt = self.persona_manager.generate_post_prompt(
            topic=topic,
            adjective=adjective,
            media_description=media_description,
            max_length=self.max_tweet_length
        )
        
        # Generate tweet
        messages = [HumanMessage(content=prompt)]
        response = await self.llm.ainvoke(messages)
        
        # Extract and clean the tweet text
        tweet_text = self._clean_tweet_text(response.content)
        
        return tweet_text
    
    async def generate_reply(self, 
                            original_tweet: str, 
                            media_description: Optional[str] = None) -> str:
        """
        Generate a reply tweet.
        
        Args:
            original_tweet: The tweet to reply to
            media_description: Description of media to include (optional)
            
        Returns:
            Generated reply text
        """
        # Generate prompt
        prompt = self.persona_manager.generate_reply_prompt(
            original_tweet=original_tweet,
            media_description=media_description,
            max_length=self.max_tweet_length
        )
        
        # Generate tweet
        messages = [HumanMessage(content=prompt)]
        response = await self.llm.ainvoke(messages)
        
        # Extract and clean the tweet text
        reply_text = self._clean_tweet_text(response.content)
        
        return reply_text
    
    async def generate_quote_tweet(self, 
                                  original_tweet: str, 
                                  media_description: Optional[str] = None) -> str:
        """
        Generate a quote tweet.
        
        Args:
            original_tweet: The tweet to quote
            media_description: Description of media to include (optional)
            
        Returns:
            Generated quote text
        """
        # For quote tweets, we'll use the same approach as reply tweets
        # but with a slightly different context
        adjective = self.persona_manager.get_random_adjective()
        
        # Generate prompt (similar to reply but with quote context)
        prompt = f"""# Task: Generate a quote tweet in the voice and style of {self.persona_manager.persona_context.agent_name}.

## Original Tweet:
{original_tweet}

## Task Details:
Write a {adjective} quote tweet that adds context, opinion, or insight to the original tweet.
Your response should be 1 or 2 sentences (choose the length at random).
Your response should not contain any questions. Brief, concise statements only.
The total character count MUST be less than {self.max_tweet_length}.
"""

        # Add media description if provided
        if media_description:
            prompt += f"""
## Media Context:
Your quote tweet should reference or relate to this media: {media_description}
Make the quote feel natural with the media, as if {self.persona_manager.persona_context.agent_name} is sharing this content.
"""
        
        # Generate tweet
        messages = [HumanMessage(content=prompt)]
        response = await self.llm.ainvoke(messages)
        
        # Extract and clean the tweet text
        quote_text = self._clean_tweet_text(response.content)
        
        return quote_text
    
    async def decide_action(self, tweet: str) -> List[str]:
        """
        Decide what action to take on a tweet.
        
        Args:
            tweet: The tweet to evaluate
            
        Returns:
            List of action tags (LIKE, RETWEET, QUOTE, REPLY)
        """
        # Generate prompt
        prompt = self.persona_manager.generate_action_prompt(tweet=tweet)
        
        # Generate decision
        messages = [HumanMessage(content=prompt)]
        response = await self.llm.ainvoke(messages)
        
        # Extract action tags
        action_tags = re.findall(r'\[(LIKE|RETWEET|QUOTE|REPLY)\]', response.content)
        
        return action_tags
    
    def _clean_tweet_text(self, text: str) -> str:
        """
        Clean and format the generated tweet text.
        
        Args:
            text: Raw generated text
            
        Returns:
            Cleaned tweet text
        """
        # Extract content from XML tags if present
        if "<post>" in text and "</post>" in text:
            pattern = r"<post>(.*?)</post>"
            matches = re.findall(pattern, text, re.DOTALL)
            if matches:
                text = matches[0].strip()
        
        # Remove any remaining XML/HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        
        # Replace escaped newlines with actual newlines
        text = text.replace("\\n\\n", "\n\n")
        
        # Ensure the text is within the character limit
        if len(text) > self.max_tweet_length:
            text = text[:self.max_tweet_length-3] + "..."
        
        return text.strip()


# Example usage
if __name__ == "__main__":
    async def main():
        # Example persona file path
        persona_file = "personas/example_persona.json"
        
        # Create tweet generator
        generator = TweetGenerator(persona_file_path=persona_file)
        
        # Generate a post
        post = await generator.generate_post(
            topic="Fitness & Workouts",
            adjective="Seductive",
            media_description="A photo of a sunset at the beach"
        )
        
        print("Generated Post:")
        print(post)
        
        # Generate a reply
        reply = await generator.generate_reply(
            original_tweet="Just finished my workout! Feeling great!",
            media_description="A selfie in workout clothes"
        )
        
        print("\nGenerated Reply:")
        print(reply)
        
        # Decide action
        tweet = "Check out my new fitness routine! It's perfect for beginners."
        actions = await generator.decide_action(tweet)
        
        print("\nDecided Actions:")
        print(actions)
    
    asyncio.run(main())

