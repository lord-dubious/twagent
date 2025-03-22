#!/usr/bin/env python
import json
import os
import math
from typing import List
from pydantic import BaseModel, Field
from crewai import LLM
from crewai.flow.flow import Flow, listen, start
import datetime  # Add this import at the top with other imports

# Convert relative path to absolute path based on the script location
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
locationToSaveGeneratedTweets = os.path.abspath(os.path.join(SCRIPT_DIR, "../../../data/generated_tweets.json"))

#

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
        
        # Adjust length for humorous tone
        target_length = state.length_category
        if state.tone == "humorous":
            # For humorous tone, aim for 1/3 of the original length
            humor_length = round(state.tweet_length / 3)
            # Recalculate the length category for humor
            category_start = math.floor(humor_length / 20) * 20
            category_end = category_start + 20
            target_length = f"{category_start+1}-{category_end}"
            print(f"Humor tone selected - adjusting length to approximately {target_length} characters")

        # Create the messages for the tweet options
        messages = [
            {"role": "system", "content": "You are a helpful assistant designed to output JSON."},
            {"role": "user", "content": f"""
            You're replying to this tweet: "{state.original_tweet}"
            
            Create 10 different reply options about "{state.topic}" with a {state.tone} tone.
            
            Make each reply have a similar length to {target_length} characters.
            The original tweet has an average word length of {state.avg_word_size:.1f} characters.
            
            For each tweet option, include only the full tweet text (match the target length of {target_length} characters)
            
            IMPORTANT REQUIREMENTS:
            1. Do not end any tweet with punctuation at the end of the last sentence.
               Example: "This is a good tweet" (correct)
               Example: "This is a good tweet." (incorrect)
            2. The first sentence of each tweet MUST be more than 20 characters long.
               Example: "This is a good first sentence. Then a second one." (correct)
               Example: "Hi there! This is the main content." (incorrect - first sentence too short)

            Make each option distinct and compelling as a direct reply to the original tweet.
            """}
        ]

        # Make the LLM call with JSON response format
        response = llm.call(messages=messages)

        # Parse the JSON response
        options_dict = json.loads(response)
        self.state.tweet_batch = TweetBatch(**options_dict)
        
        # Remove trailing punctuation from all tweets
        for option in self.state.tweet_batch.tweet_options:
            option.tweet_text = option.tweet_text.rstrip('.,!?;:')
            
            # Validate first sentence length (fallback check)
            first_sentence_end = option.tweet_text.find('.')
            if first_sentence_end != -1 and first_sentence_end < 20:
                # Add filler to make first sentence longer if it's too short
                parts = option.tweet_text.split('.', 1)
                option.tweet_text = parts[0] + " actually" + ("." + parts[1] if len(parts) > 1 else "")

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
                
                # Check if the directory exists, if not, create it
                directory = os.path.dirname(locationToSaveGeneratedTweets)
                if not os.path.exists(directory):
                    os.makedirs(directory)
                    
                # Save the selected tweet to a file
                with open(locationToSaveGeneratedTweets, "w") as f:
                    tweet_dict = {
                        "original_tweet": self.state.original_tweet,
                        "reply": self.state.selected_tweet.model_dump()
                    }
                    json.dump(tweet_dict, f, indent=2)
                
                print(f"\nTweet reply selected and saved to: {locationToSaveGeneratedTweets}")
                return self.state.selected_tweet
            
            else:
                print("Invalid selection. Please try again.")

    @listen(select_tweet)
    def save_selected_tweet(self, selected_tweet):
        """Save the selected tweet to a JSON file by appending it"""
        print("\nSaving your selected tweet reply...")
                
        output_file = locationToSaveGeneratedTweets
        print(f"Attempting to save to: {output_file}")
        print(f"Script directory: {SCRIPT_DIR}")
        print(f"Absolute path: {os.path.abspath(output_file)}")
        
        # Get the current date and time in ISO format
        current_date = datetime.datetime.now().isoformat()
        
        # Create new tweet data
        new_tweet_data = {
            "original_tweet": self.state.original_tweet,
            "reply": {
                "tweet_text": selected_tweet.tweet_text,
                "date_created": current_date
            }
        }

        try:
            # Create directory if it doesn't exist
            directory = os.path.dirname(output_file)
            if directory and not os.path.exists(directory):
                print(f"Creating directory: {directory}")
                os.makedirs(directory, exist_ok=True)
            
            # Simply write the tweet to the file, creating a new file if necessary
            if not os.path.exists(output_file) or os.path.getsize(output_file) == 0:
                # File doesn't exist or is empty - create new file with array
                print(f"Creating new file at {output_file}")
                with open(output_file, "w", encoding="utf-8") as f:
                    json.dump([new_tweet_data], f, indent=2)
                print(f"Created new file with tweet")
            else:
                # File exists - try to append
                try:
                    # First read existing data
                    with open(output_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        if not isinstance(data, list):
                            data = [data]
                    
                    # Append new data and write back
                    data.append(new_tweet_data)
                    with open(output_file, "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=2)
                    print(f"Appended tweet to existing file")
                    
                except json.JSONDecodeError:
                    # Invalid JSON - overwrite with just this tweet
                    print(f"File contains invalid JSON, creating new file")
                    with open(output_file, "w", encoding="utf-8") as f:
                        json.dump([new_tweet_data], f, indent=2)
        except Exception as e:
            print(f"Error saving tweet: {str(e)}")
            import traceback
            traceback.print_exc()
            
            # Check if locationToSaveGeneratedTweets is properly defined
            print(f"Output file path: {output_file}")
            print(f"Directory exists: {os.path.exists(os.path.dirname(output_file)) if os.path.dirname(output_file) else 'No directory specified'}")
            print(f"Current working directory: {os.getcwd()}")
            
            # Try saving to a fallback location in the current directory
            fallback_file = "saved_tweets.json"
            try:
                print(f"Trying fallback location: {fallback_file}")
                with open(fallback_file, "w", encoding="utf-8") as f:
                    json.dump([new_tweet_data], f, indent=2)
                print(f"Saved to fallback location: {fallback_file}")
            except Exception as e2:
                print(f"Fallback also failed: {str(e2)}")
        
        return selected_tweet

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