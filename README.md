# Project Overview

This repository leverages the `browser_use` library to search tweets on Twitter, save them to a database, and use this data to send real-time tweets. This approach was chosen as a solution because the Twitter API is prohibitively expensive and is often seen as anti-developer.

## How to Run This Repository

### Prerequisites
- Python 3.8 or higher
- Chrome browser installed (for browser-use)


### Installation

1. Clone this repository. Then, install browser-use and playwright:
```
pip install browser-use
playwright install

```
2. Add your API keys for the provider you want to use to your .env file. 

3. Set up Twitter authentication:
   - Create a `twitter_cookies.txt` file in the root directory
   - Format the cookies file as shown below:
   ```json
   [{
       "name": "auth_token",
       "value": "YOUR_AUTH_TOKEN",
       "domain": ".x.com",
       "path": "/"
     },
   {
       "name": "ct0",
       "value": "YOUR_CT0_TOKEN",
       "domain": ".x.com",
       "path": "/"
   }]
   ```
   - You can obtain these cookies by logging into Twitter in your browser and extracting them using browser developer tools

### Usage

Run the main script to fetch the latest tweets from a specific Twitter profile:


This will:
1. Open a browser session
2. Navigate to the specified Twitter profile (currently set to DOGE's profile)
3. Extract the latest tweets
4. Save them to `saved_tweets.json`