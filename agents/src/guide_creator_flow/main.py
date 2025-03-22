#!/usr/bin/env python
import json
import os
import math
from typing import List
from pydantic import BaseModel, Field
from crewai import LLM
from crewai.flow.flow import Flow, listen, start

# Define our models for structured data
class TweetOption(BaseModel):
    tweet_text: str = Field(description="The full text of the tweet")

class TweetBatch(BaseModel):
    tweet_options: List[TweetOption] = Field(description="List of tweet options to choose from")

# Define our flow state
class TweetCreatorState(BaseModel):
    topic: str = ""
    tone: str = ""
    original_tweet: str = ""
    tweet_length: int = 0
    avg_word_size: float = 0
    length_category: str = ""
    tweet_batch: TweetBatch = None
    selected_tweet: TweetOption = None

class TweetCreatorFlow(Flow[TweetCreatorState]):
    """Flow for creating tweets"""

    @start()
    def get_user_input(self):
        """Get input from the user about the tweet topic, tone, and original tweet to reply to"""
        print("\n=== Create Your Engaging Tweet Reply ===\n")

        # Get original tweet to reply to
        self.state.original_tweet = input("Enter the tweet you want to reply to: ")
        
        # Calculate tweet metrics
        self.state.tweet_length = len(self.state.original_tweet)
        
        # Calculate average word size
        words = self.state.original_tweet.split()
        if words:
            self.state.avg_word_size = sum(len(word) for word in words) / len(words)
        else:
            self.state.avg_word_size = 0
            
        # Determine length category (0-20, 21-40, 41-60, etc.)
        category_start = math.floor(self.state.tweet_length / 20) * 20
        category_end = category_start + 20
        self.state.length_category = f"{category_start+1}-{category_end}"
        
        # Get topic for the reply
        self.state.topic = input("What topic would you like to focus on in your reply? ")

        # Get tone with validation
        while True:
            tone = input("What tone would you like? (professional/casual/humorous) ").lower()
            if tone in ["professional", "casual", "humorous"]:
                self.state.tone = tone
                break
            print("Please enter 'professional', 'casual', or 'humorous'")

        print(f"\nOriginal tweet is {self.state.tweet_length} characters with avg word size of {self.state.avg_word_size:.1f}")
        print(f"Length category: {self.state.length_category} characters")
        print(f"Creating 10 reply options on {self.state.topic} with a {self.state.tone} tone...\n")
        return self.state

    @listen(get_user_input)
    def generate_tweet_options(self, state):
        """Generate multiple tweet reply options using an LLM"""
        print("Generating tweet reply options...")

        # Initialize the LLM
        llm = LLM(model="openai/gpt-4o-mini", response_format=TweetBatch)

        # Create the messages for the tweet options
        messages = [
            {"role": "system", "content": "You are a helpful assistant designed to output JSON."},
            {"role": "user", "content": f"""
            You're replying to this tweet: "{state.original_tweet}"
            
            Create 10 different reply options about "{state.topic}" with a {state.tone} tone.
            
            Make each reply have a similar length to the original tweet (approximately {state.length_category} characters).
            The original tweet has an average word length of {state.avg_word_size:.1f} characters.
            
            For each tweet option, include only the full tweet text (match the length category of {state.length_category} characters)

            Make each option distinct and compelling as a direct reply to the original tweet.
            """}
        ]

        # Make the LLM call with JSON response format
        response = llm.call(messages=messages)

        # Parse the JSON response
        options_dict = json.loads(response)
        self.state.tweet_batch = TweetBatch(**options_dict)

        print(f"Generated {len(self.state.tweet_batch.tweet_options)} tweet reply options")
        return self.state.tweet_batch

    @listen(generate_tweet_options)
    def select_tweet(self, tweet_batch):
        """Let the user select a tweet or generate new options"""
        print("\n=== Tweet Reply Options ===\n")
        print(f"Original Tweet: {self.state.original_tweet}\n")

        while True:
            # Display all tweet options
            for i, option in enumerate(tweet_batch.tweet_options, 1):
                print(f"\nOption {i} ({len(option.tweet_text)} chars):")
                print(f"Reply: {option.tweet_text}")
                print("-" * 50)

            # Get user selection
            selection = input("\nSelect a reply (1-10), or type 'new' for new options, or 'exit' to quit: ")
            
            if selection.lower() == 'new':
                # Generate new options
                return self.generate_tweet_options(self.state)
            
            elif selection.lower() == 'exit':
                print("Exiting without selecting a tweet reply.")
                return None
            
            elif selection.isdigit() and 1 <= int(selection) <= len(tweet_batch.tweet_options):
                # Select the chosen tweet
                selected_index = int(selection) - 1
                self.state.selected_tweet = tweet_batch.tweet_options[selected_index]
                
                # Create output directory if it doesn't exist
                os.makedirs("output", exist_ok=True)
                
                # Save the selected tweet to a file
                with open("output/selected_tweet_reply.json", "w") as f:
                    tweet_dict = {
                        "original_tweet": self.state.original_tweet,
                        "reply": self.state.selected_tweet.model_dump()
                    }
                    json.dump(tweet_dict, f, indent=2)
                
                print(f"\nTweet reply selected and saved to output/selected_tweet_reply.json")
                return self.state.selected_tweet
            
            else:
                print("Invalid selection. Please try again.")

def kickoff():
    """Run the tweet creator flow"""
    result = TweetCreatorFlow().kickoff()
    if result:
        print("\n=== Flow Complete ===")
        print(f"Your tweet reply is ready: {result.tweet_text}")
    else:
        print("\n=== Flow Cancelled ===")

def plot():
    """Generate a visualization of the flow"""
    flow = TweetCreatorFlow()
    flow.plot("tweet_creator_flow")
    print("Flow visualization saved to tweet_creator_flow.html")

if __name__ == "__main__":
    kickoff()