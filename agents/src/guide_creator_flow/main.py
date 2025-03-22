#!/usr/bin/env python
import json
import os
import math
from typing import List
from pydantic import BaseModel, Field
from crewai import LLM
from crewai.flow.flow import Flow, listen, start
import random
import datetime  # Add this import at the top with other imports
from guide_creator_flow.crews.tweet_generator_crew.content_crew import TweetGeneratorCrew
from guide_creator_flow.utils.browser_subprocess import call_twitter_reply_script

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
    def get_last_saved_tweet(self):
        """Retrieve the last saved tweet from the saved_tweets.json file"""
        try:
            with open(os.path.join(SCRIPT_DIR, "../../../data/saved_tweets.json"), "r") as f:
                data = json.load(f)
                if data and "tweets" in data and data["tweets"]:
                    last_tweet = data["tweets"][-1]
                    print("Last saved tweet retrieved successfully.")
                    print(f"Last Tweet: {last_tweet}")
                    # Get original tweet to reply to
                    self.state.original_tweet = last_tweet.get("text", "")
                    
                    # Calculate tweet metrics
                    self.state.tweet_length = len(self.state.original_tweet)
                    
                    # Calculate average word size
                    words = self.state.original_tweet
                    if words:
                        self.state.avg_word_size = sum(len(word) for word in words) / len(words)
                    else:
                        self.state.avg_word_size = 0
                        
                    # Determine length category (0-20, 21-40, 41-60, etc.)
                    category_start = math.floor(self.state.tweet_length / 20) * 20
                    category_end = category_start + 20
                    self.state.length_category = f"{category_start+1}-{category_end}"
                    
                    self.state.topic = "funny"

                    # Get tone with validation
                    self.state.tone = random.choice(["professional", "casual", "humorous"])
                    print(f"Randomly selected tone: {self.state.tone}")

                    print(f"\nOriginal tweet is {self.state.tweet_length} characters with avg word size of {self.state.avg_word_size:.1f}")
                    print(f"Length category: {self.state.length_category} characters")
                    print(f"Creating 10 reply options on {self.state.topic} with a {self.state.tone} tone...\n")
                    return self.state
                else:
                    print("No tweets found in the saved_tweets.json file.")
                    return None
        except FileNotFoundError:
            print("The saved_tweets.json file does not exist.")
            return None
        except json.JSONDecodeError:
            print("Error decoding the saved_tweets.json file.")
            return None


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



    @listen(get_last_saved_tweet)
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
            
            Make each option distinct and compelling as a direct reply to the original tweet.
            """}
        ]

        # Make the LLM call with JSON response format
        #response = TweetGeneratorCrew().crew().kickoff(inputs=messages)
        response = llm.call(messages=messages)

        # Parse the JSON response
        options_dict = json.loads(response)
        self.state.tweet_batch = TweetBatch(**options_dict)
        
        # Process all tweets for formatting requirements
        for option in self.state.tweet_batch.tweet_options:
            # Remove trailing punctuation
            option.tweet_text = option.tweet_text.rstrip('.,!?;:')
            
            # Replace all exclamation points with periods
            option.tweet_text = option.tweet_text.replace('!', '.')
            
            # Validate first sentence length using multiple sentence endings
            first_sentence_end = min(
                (pos for pos in [
                    option.tweet_text.find('.'), 
                    option.tweet_text.find('?')
                ] if pos != -1),
                default=-1
            )
            # Check if the first sentence is less than 20 characters
            if first_sentence_end != -1 and first_sentence_end < 20:
                second_sentence_start = option.tweet_text.find(' ', first_sentence_end + 1)
                if second_sentence_start != -1:
                    option.tweet_text = option.tweet_text[second_sentence_start + 1:]

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
                
                # Get the current date and time in ISO format
                current_date = datetime.datetime.now().isoformat()
                
                # Prepare data to save
                tweet_dict = {
                    "original_tweet": self.state.original_tweet,
                    "reply": {
                        "tweet_text": self.state.selected_tweet.tweet_text,
                        "date_created": current_date
                    }
                }

                # Load existing data if file exists
                existing_data = []
                if os.path.exists(locationToSaveGeneratedTweets) and os.path.getsize(locationToSaveGeneratedTweets) > 0:
                    try:
                        with open(locationToSaveGeneratedTweets, "r") as f:
                            existing_data = json.load(f)
                            # Convert to list if it's a single object
                            if not isinstance(existing_data, list):
                                existing_data = [existing_data]
                    except json.JSONDecodeError:
                        print("Error reading existing file. Starting with empty list.")

                # Append new data
                existing_data.append(tweet_dict)

                # Make sure directory exists
                directory = os.path.dirname(locationToSaveGeneratedTweets)
                if directory and not os.path.exists(directory):
                    os.makedirs(directory)

                # Save updated data
                with open(locationToSaveGeneratedTweets, "w") as f:
                    json.dump(existing_data, f, indent=2)
                    print(f"\nTweet reply selected and saved to: {locationToSaveGeneratedTweets}")

                return self.state.selected_tweet
            
            else:
                print("Invalid selection. Please try again.")

    
    @listen(select_tweet)
    def post_tweet(self, selected_tweet):
        """Display the tweet dictionary and call the Twitter reply script"""
        if selected_tweet:
            # Get the current date and time in ISO format (same as in select_tweet)
            current_date = datetime.datetime.now().isoformat()
            
            # Recreate the tweet_dict structure
            tweet_dict = {
                "original_tweet": self.state.original_tweet,
                "reply": {
                    "tweet_text": selected_tweet.tweet_text,
                    "date_created": current_date
                }
            }
            
            print("\n=== Tweet Dictionary Details ===")
            print(f"Original tweet: {tweet_dict['original_tweet']}")
            print(f"Reply text: {tweet_dict['reply']['tweet_text']}")
            print(f"Date created: {tweet_dict['reply']['date_created']}")
            
            # Ask the user if they want to post this tweet as a reply on Twitter
            post_to_twitter = input("\nWould you like to post this as a reply on Twitter? (yes/no): ")
            
            if post_to_twitter.lower() in ['yes', 'y']:
                # Call the utility function to handle Twitter reply via subprocess
                call_twitter_reply_script(selected_tweet.tweet_text)
            else:
                print("Tweet not posted to Twitter.")
        else:
            print("No tweet was selected.")

        return selected_tweet

def kickoff():
    """Run the tweet creator flow"""
    result = TweetCreatorFlow().kickoff()
    if result:
        print("\n=== Flow Complete ===")
        if hasattr(result, 'tweet_text'):
            print(f"Your tweet reply is ready: {result.tweet_text}")
        elif isinstance(result, TweetCreatorState) and result.selected_tweet:
            print(f"Your tweet reply is ready: {result.selected_tweet.tweet_text}")
        else:
            print("Tweet created successfully.")
    else:
        print("\n=== Flow Cancelled ===")

def plot():
    """Generate a visualization of the flow"""
    flow = TweetCreatorFlow()
    flow.plot("tweet_creator_flow")
    print("Flow visualization saved to tweet_creator_flow.html")

if __name__ == "__main__":
    kickoff()