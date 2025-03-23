#!/usr/bin/env python
import json
import os
import math
from typing import List
from pydantic import BaseModel, Field
import random
import datetime  # Add this import at the top with other imports
from openai import OpenAI
from dotenv import load_dotenv  # Add this import

load_dotenv()

SCRIPT_DIR = os.path.dirname(__file__)

pathToData = "../data"
lastSavedTweets = "/001_saved_tweets.json"


# Define the Tweet model
class Tweet(BaseModel):
    tweet_text: str

class TweetOptions(BaseModel):
    tweet_options: List[Tweet]
    
# Define our flow state
class TweetCreatorState(BaseModel):
    original_tweet: str = ""
    tweet_url: str = ""
    tweet_length: int = 0
    avg_word_size: float = 0
    topic: str = ""
    tone: str = ""

    
    length_category: str = ""
    tweet_batch: TweetOptions = None
    selected_tweet: Tweet = None
    
# Simple LLM mock class for generating responses
class LLM:
    def __init__(self, model, response_format=None):
        self.model = model
        self.response_format = response_format
        
    def call(self, messages):
        # Real implementation that calls OpenAI API
        
        try:
            # Get API key from environment variable
            api_key = os.environ.get("OPENAI_API_KEY")
                
            client = OpenAI(api_key=api_key)
            
            completion = client.chat.completions.create(
                model="gpt-4o-mini-2024-07-18",
                messages=messages,  # Use the messages passed to the function
                response_format={"type": "json_object"}  # Request JSON response format
            )
            print(completion.choices[0].message.content)
            # Extract the content from the response
            return completion.choices[0].message.content
            
        except Exception as e:
            print(f"Error calling OpenAI API: {str(e)}")
            
            # Fallback to mock response if API call fails
            options = []
            for i in range(10):
                options.append({
                    "tweet_text": f"hmm {i+1}."
                })
            return json.dumps({"tweet_options": options})

class TweetCreatorFlow:
    def __init__(self):
        """Initialize the TweetCreatorFlow with a default state."""
        self.state = TweetCreatorState()

    def kickoff(self):
        """Start the workflow"""
        # Try to get the last saved tweet first
        if True:
            self.get_last_saved_tweet()
            tweet_batch = self.generate_tweet_options(self.state)
        else:
            # If no saved tweet, get user input
            self.get_user_input()
            tweet_batch = self.generate_tweet_options(self.state)
        
        self.select_tweet(tweet_batch)
        return self.post_tweet()

    def get_last_saved_tweet(self):
        """Retrieve the last saved tweet from the saved_tweets.json file"""
        try:
            with open(os.path.join(SCRIPT_DIR, pathToData + lastSavedTweets), "r") as f:
                data = json.load(f)
                if data and "tweets" in data and data["tweets"]:
                    last_tweet = data["tweets"][-1]
                    print("Last saved tweet retrieved successfully.")
                    print(f"Last Tweet: {last_tweet}")
                    # Get original tweet to reply to
                    self.state.original_tweet = last_tweet.get("text", "")
                    self.state.tweet_url = last_tweet.get("tweet_link", "")

                    # Calculate tweet metrics
                    self.state.tweet_length = len(self.state.original_tweet)
                    
                    # Calculate average word size
                    words = self.state.original_tweet.split()  # Fixed: need to split into words
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
                    return True
                else:
                    print("No tweets found in the saved_tweets.json file.")
                    return False
        except FileNotFoundError:
            print("The saved_tweets.json file does not exist.")
            return False
        except json.JSONDecodeError:
            print("Error decoding the saved_tweets.json file.")
            return False

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

    def generate_tweet_options(self, state):
        """Generate multiple tweet reply options using an LLM"""
        print("Generating tweet reply options...")
        
        # Initialize the LLM
        llm = LLM(model="openai/gpt-4o-mini", response_format=TweetOptions)
        
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
            
            Format your response as a JSON object with a key "tweet_options" containing an array of objects, 
            each with a "tweet_text" field.
            """}
        ]

        # Make the LLM call with JSON response format
        response = llm.call(messages=messages)
        
        # Parse the JSON response
        response_dict = json.loads(response)
        
        # Transform the response if needed to match our expected structure
        if "tweet_options" not in response_dict and "replies" in response_dict:
            # Convert "replies" to the expected "tweet_options" format
            tweet_options = []
            for reply in response_dict["replies"]:
                tweet_options.append({"tweet_text": reply})
            response_dict = {"tweet_options": tweet_options}
        
        # Handle any other potential response format
        if "tweet_options" not in response_dict:
            # Create a fallback structure with whatever data we can find
            tweet_options = []
            # Look through the response for any arrays that might contain our tweets
            for key, value in response_dict.items():
                if isinstance(value, list) and len(value) > 0:
                    if isinstance(value[0], dict) and "tweet_text" in value[0]:
                        # We found our tweet options
                        tweet_options = value
                        break
                    elif isinstance(value[0], str):
                        # Convert strings to tweet objects
                        tweet_options = [{"tweet_text": text} for text in value]
                        break
            
            # If we still don't have options, create empty ones as a last resort
            if not tweet_options:
                tweet_options = [{"tweet_text": f"Reply option {i+1}"} for i in range(10)]
            
            response_dict = {"tweet_options": tweet_options}
        
        self.state.tweet_batch = TweetOptions(**response_dict)
        
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
                    
                    "tweet_text": self.state.original_tweet,
                    "tweet_url": self.state.tweet_url,
                    "reply": {
                        "tweet_text": self.state.selected_tweet.tweet_text,
                        "date_created": current_date
                    }
                }

                # Load existing data if file exists
                existing_data = []
                if os.path.exists(pathToData+generatedTweets) and os.path.getsize(pathToData+generatedTweets) > 0:
                    try:
                        with open(pathToData+generatedTweets, "r") as f:
                            existing_data = json.load(f)
                            # Convert to list if it's a single object
                            if not isinstance(existing_data, list):
                                existing_data = [existing_data]
                    except json.JSONDecodeError:
                        print("Error reading existing file. Starting with empty list.")

                # Append new data
                existing_data.append(tweet_dict)

                # Make sure directory exists
                directory = os.path.dirname(pathToData+generatedTweets)
                if directory and not os.path.exists(directory):
                    os.makedirs(directory)

                # Save updated data
                with open(pathToData+generatedTweets, "w") as f:
                    json.dump(existing_data, f, indent=2)
                    print(f"\nTweet reply selected and saved to: {pathToData+generatedTweets}")
            
            else:
                print("Invalid selection. Please try again.")
            return

    def find_tweets(self):
        try:
            with open(os.path.join(SCRIPT_DIR, pathToData + generatedTweets), "r") as f:
                data = json.load(f)
                if data:
                    last_reply = data[-1]
                    print("Last saved reply retrieved successfully.")
                    print(f"Last Reply: {last_reply}")
                    # Prepare data to save
                    posted_tweet_dict = {
                        "tweet_url": last_reply["tweet_url"],
                        "tweet_text": last_reply["tweet_text"],
                        "reply_text": last_reply["reply"]["tweet_text"],
                        "reply_time": last_reply["reply"]["date_created"]
                    }

                    from my_twitter_api_v3.manage_posts.reply_to_post import reply_to_post
                    import asyncio
                    asyncio.run(reply_to_post(tweet_url=last_reply["tweet_url"], my_post=last_reply["reply"]["tweet_text"]))



        except FileNotFoundError:
            print("The generated_tweets.json file does not exist.")
            return False
        except json.JSONDecodeError:
            print("Error decoding the generated_tweets.json file.")
            return False


if __name__ == "__main__":
    workflow = TweetCreatorFlow()
    workflow.kickoff()