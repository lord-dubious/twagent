from playwright.sync_api import sync_playwright
from pydantic import BaseModel
import json
import os
import pathlib
import time

class Tweet(BaseModel):
    tweet_url: str

class Tweets(BaseModel):
    tweets: list[Tweet]

def load_cookies():
    """Load Twitter cookies from a file."""
    current_dir = pathlib.Path(__file__).parent
    parent_dir = current_dir.parent
    cookie_path = parent_dir / "twitter_cookies.txt"
    
    with open(cookie_path, "r") as f:
        cookies_data = f.read()
    
    return json.loads(cookies_data)

def get_list_posts(list_id = "1136636450206900225"):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # Set to False to see browser
        context = browser.new_context()
        page = context.new_page()

        # Load cookies
        cookies = load_cookies()
        context.add_cookies(cookies)

        # Navigate to Twitter List
        page.goto(f"https://twitter.com/i/lists/{list_id}", wait_until="load")

        # Wait for tweets to load
        page.wait_for_selector("article")

        # Scroll once to load more content
        page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
        time.sleep(3)  # Wait for new tweets to load

        # Extract tweet URLs - fix the selector line
        tweet_urls = set()
        tweets = page.query_selector_all("article a[href*='/status/']")
        
        for tweet in tweets:
            href = tweet.get_attribute("href")
            if href:
                full_url = "https://twitter.com" + href
                tweet_urls.add(full_url)

        browser.close()

    # Create a list to hold tweet dictionaries
    tweet_dicts = []
    
    for url in tweet_urls:

        if url.endswith("/photo/1"):
            url = url[:-len("/photo/1")]
        elif url.endswith("/photo/2"):
            url = url[:-len("/photo/2")]
        elif url.endswith("/analytics"):
            url = url[:-len("/analytics")]
        tweet_dict = {
            "handle": "",  # Placeholder for the tweet handle
            "datetime": "",  # Placeholder for the tweet datetime
            "text": "",  # Placeholder for the tweet text
            "likes": "",  # Placeholder for the number of likes
            "retweets": "",  # Placeholder for the number of retweets
            "replies": "",  # Placeholder for the number of replies
            "bookmarks": "",  # Placeholder for the number of bookmarks
            "viewcount": "",  # Placeholder for the view count
            "tweet_url": url  # The tweet URL
        }
        tweet_dicts.append(tweet_dict)

    # Create a structured data object
    parsed = {"tweets": tweet_dicts}

    print(json.dumps(parsed, indent=4))  # Print JSON output
    return parsed["tweets"]  # Return just the tweets array to match expected format

if __name__ == "__main__":
    get_list_posts()
