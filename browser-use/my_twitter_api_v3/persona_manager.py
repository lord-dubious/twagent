#!/usr/bin/env python3
"""
Persona Manager for Twitter Automation

This module handles persona management for Twitter automation, including:
- Loading and parsing persona data from JSON files
- Generating prompts for LLM-based content creation
- Supporting media tweets and persona-based interactions
"""

import json
import os
import random
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass


@dataclass
class PersonaContext:
    """Context data for persona-based content generation"""
    agent_name: str
    twitter_username: str
    system: str
    bio: str
    lore: str
    adjectives: List[str]
    topics: List[str]
    post_examples: List[str]
    message_examples: List[List[Dict[str, Any]]]
    style: Dict[str, List[str]]


class PersonaManager:
    """
    Manages persona data and content generation for Twitter automation.
    
    This class handles loading persona data from JSON files, generating
    prompts for LLM-based content creation, and supporting media tweets
    and persona-based interactions.
    """

    def __init__(self, persona_file_path: Optional[str] = None):
        """
        Initialize the persona manager.
        
        Args:
            persona_file_path: Path to the persona JSON file (optional)
        """
        self.persona_file_path = persona_file_path
        self.persona_data = None
        self.persona_context = None
        
        if persona_file_path:
            self.load_persona(persona_file_path)
    
    def load_persona(self, file_path: str) -> bool:
        """
        Load persona data from a JSON file.
        
        Args:
            file_path: Path to the persona JSON file
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.persona_data = json.load(f)
            
            # Create persona context
            self.persona_context = self._create_persona_context(self.persona_data)
            return True
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error loading persona data: {e}")
            return False
    
    def _create_persona_context(self, data: Dict[str, Any]) -> PersonaContext:
        """
        Create a persona context from the loaded data.
        
        Args:
            data: Persona data dictionary
            
        Returns:
            PersonaContext: Structured persona context
        """
        # Get agent name (handle both formats)
        agent_name = data.get("name", data.get("agent name", ""))
        
        # Get Twitter username (default to agent name if not specified)
        twitter_username = data.get("twitter_username", agent_name)
        
        # Get system prompt
        system = data.get("system", "")
        
        # Format bio - handle both string and array formats
        bio_data = data.get("bio", [])
        bio = "\n".join(bio_data) if isinstance(bio_data, list) else str(bio_data)
        
        # Format lore
        lore_data = data.get("lore", [])
        lore = "\n".join(lore_data) if isinstance(lore_data, list) else str(lore_data)
        
        # Get adjectives
        adjectives = data.get("adjectives", [])
        
        # Get topics
        topics = data.get("topics", [])
        
        # Get post examples
        post_examples = data.get("postExamples", [])
        
        # Get message examples
        message_examples = data.get("messageExamples", [])
        
        # Get style guidelines
        style = data.get("style", {})
        
        return PersonaContext(
            agent_name=agent_name,
            twitter_username=twitter_username,
            system=system,
            bio=bio,
            lore=lore,
            adjectives=adjectives,
            topics=topics,
            post_examples=post_examples,
            message_examples=message_examples,
            style=style
        )
    
    def get_random_examples(self, count: int = 2) -> List[List[Dict[str, Any]]]:
        """
        Get random message examples from the persona.
        
        Args:
            count: Number of examples to return
            
        Returns:
            List of message example sequences
        """
        if not self.persona_context or not self.persona_context.message_examples:
            return []
        
        examples = self.persona_context.message_examples
        if count >= len(examples):
            return examples
        
        return random.sample(examples, count)
    
    def get_random_topic(self) -> str:
        """
        Get a random topic from the persona.
        
        Returns:
            Random topic string
        """
        if not self.persona_context or not self.persona_context.topics:
            return ""
        
        return random.choice(self.persona_context.topics)
    
    def get_random_adjective(self) -> str:
        """
        Get a random adjective from the persona.
        
        Returns:
            Random adjective string
        """
        if not self.persona_context or not self.persona_context.adjectives:
            return ""
        
        return random.choice(self.persona_context.adjectives)
    
    def generate_post_prompt(self, topic: Optional[str] = None, adjective: Optional[str] = None, 
                            media_description: Optional[str] = None, max_length: int = 280) -> str:
        """
        Generate a prompt for creating a post.
        
        Args:
            topic: Topic to post about (random if None)
            adjective: Adjective to describe the post (random if None)
            media_description: Description of media to include (optional)
            max_length: Maximum length of the post
            
        Returns:
            Prompt string for LLM
        """
        if not self.persona_context:
            return ""
        
        # Get random topic and adjective if not provided
        if not topic:
            topic = self.get_random_topic()
        
        if not adjective:
            adjective = self.get_random_adjective()
        
        # Format post examples
        post_examples = "\n".join([f"- {example}" for example in self.persona_context.post_examples[:5]])
        
        # Format style guidelines
        all_style = "\n".join([f"- {guideline}" for guideline in self.persona_context.style.get("all", [])])
        post_style = "\n".join([f"- {guideline}" for guideline in self.persona_context.style.get("post", [])])
        
        # Build the prompt
        prompt = f"""# Task: Generate a post in the voice, style, and perspective of {self.persona_context.agent_name} (@{self.persona_context.twitter_username}).

## About {self.persona_context.agent_name}:
{self.persona_context.system}

## Bio:
{self.persona_context.bio}

## Style Guidelines:
{all_style}

## Post Style:
{post_style}

## Post Examples:
{post_examples}

## Task Details:
Write a post that is {adjective} about {topic} (without mentioning {topic} directly), from the perspective of {self.persona_context.agent_name}.
Your response should be 1, 2, or 3 sentences (choose the length at random).
Your response should not contain any questions. Brief, concise statements only.
The total character count MUST be less than {max_length}.
Use "\\n\\n" (double spaces) between statements if there are multiple statements in your response.
"""

        # Add media description if provided
        if media_description:
            prompt += f"""
## Media Context:
Your post should reference or relate to this media: {media_description}
Make the post feel natural with the media, as if {self.persona_context.agent_name} is sharing this content.
"""

        return prompt
    
    def generate_reply_prompt(self, original_tweet: str, media_description: Optional[str] = None, 
                             max_length: int = 280) -> str:
        """
        Generate a prompt for creating a reply to a tweet.
        
        Args:
            original_tweet: The tweet to reply to
            media_description: Description of media to include (optional)
            max_length: Maximum length of the reply
            
        Returns:
            Prompt string for LLM
        """
        if not self.persona_context:
            return ""
        
        # Get random adjective
        adjective = self.get_random_adjective()
        
        # Format style guidelines
        all_style = "\n".join([f"- {guideline}" for guideline in self.persona_context.style.get("all", [])])
        chat_style = "\n".join([f"- {guideline}" for guideline in self.persona_context.style.get("chat", [])])
        
        # Build the prompt
        prompt = f"""# Task: Generate a reply tweet in the voice, style, and perspective of {self.persona_context.agent_name} (@{self.persona_context.twitter_username}).

## About {self.persona_context.agent_name}:
{self.persona_context.system}

## Bio:
{self.persona_context.bio}

## Style Guidelines:
{all_style}

## Chat Style:
{chat_style}

## Original Tweet:
{original_tweet}

## Task Details:
Write a {adjective} reply to the above tweet from the perspective of {self.persona_context.agent_name}.
Your reply should be a direct response to the original tweet.
Your response should be 1 or 2 sentences (choose the length at random).
Your response should not contain any questions. Brief, concise statements only.
The total character count MUST be less than {max_length}.
Use "\\n\\n" (double spaces) between statements if there are multiple statements in your response.
"""

        # Add media description if provided
        if media_description:
            prompt += f"""
## Media Context:
Your reply should reference or relate to this media: {media_description}
Make the reply feel natural with the media, as if {self.persona_context.agent_name} is sharing this content in response.
"""

        return prompt
    
    def generate_action_prompt(self, tweet: str) -> str:
        """
        Generate a prompt for deciding what action to take on a tweet.
        
        Args:
            tweet: The tweet to evaluate
            
        Returns:
            Prompt string for LLM
        """
        if not self.persona_context:
            return ""
        
        # Format topics
        topics = "\n".join([f"- {topic}" for topic in self.persona_context.topics])
        
        # Build the prompt
        prompt = f"""# INSTRUCTIONS: Determine actions for {self.persona_context.agent_name} (@{self.persona_context.twitter_username}) based on:

## About {self.persona_context.agent_name}:
{self.persona_context.system}

## Bio:
{self.persona_context.bio}

## Topics of Interest:
{topics}

## Guidelines:
- ONLY engage with content that DIRECTLY relates to character's core interests
- Direct mentions are priority IF they are on-topic
- Skip ALL content that is:
  - Off-topic or tangentially related
  - From high-profile accounts unless explicitly relevant
  - Generic/viral content without specific relevance
  - Political/controversial unless central to character
  - Promotional/marketing unless directly relevant

## Actions (respond only with tags):
[LIKE] - Perfect topic match AND aligns with character (9.8/10)
[RETWEET] - Exceptional content that embodies character's expertise (9.5/10)
[QUOTE] - Can add substantial domain expertise (9.5/10)
[REPLY] - Can contribute meaningful, expert-level insight (9.5/10)

## Tweet:
{tweet}

# Respond with qualifying action tags only. Default to NO action unless extremely confident of relevance.
"""
        
        return prompt
    
    def save_persona_to_file(self, file_path: str) -> bool:
        """
        Save the current persona data to a JSON file.
        
        Args:
            file_path: Path to save the persona JSON file
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.persona_data:
            return False
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.persona_data, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving persona data: {e}")
            return False


# Example usage
if __name__ == "__main__":
    # Example persona file path
    persona_file = "personas/example_persona.json"
    
    # Create persona manager
    manager = PersonaManager(persona_file)
    
    # Generate a post prompt
    post_prompt = manager.generate_post_prompt(
        topic="Fitness & Workouts",
        adjective="Seductive",
        media_description="A photo of a sunset at the beach"
    )
    
    print(post_prompt)

