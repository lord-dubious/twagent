# Project Overview

This repository leverages AI agents (w/ `browser_use`, `elevenlabs`) to monitor twitter accounts, analyze trends, score tweets, reply/post/retweet, and speak in twitter spaces.


The workflow is designed for pseudosatirical social causes. It aims to create provocative arguments and pick fights online.


## Key Features

- **Twitter Monitoring**: Monitor Twitter accounts and analyze trends
- **Tweet Analysis**: Score tweets based on relevance and engagement potential
- **Automated Interactions**: Reply, post, and retweet content
- **Twitter Spaces**: Participate in Twitter Spaces with voice capabilities
- **Follower Automation**: Target and follow users based on specific criteria
- **Persona-Based Tweets**: Generate tweets in the voice and style of specific personas, with support for media tweets


## Why browser-use? Why not just use Twitter's V2 API?

This approach was chosen as a solution because the Twitter API is prohibitively expensive and is often seen as anti-developer.

- **Frequent API Changes**: Pricing, access levels, and endpoints have changed unpredictably. Some previously available endpoints have been removed or moved to higher-cost tiers.
- **Expensive Paid Tiers**: Free-tier access is very limited, and paid tiers are costly.
- **Rate Limits & Downtime**: Even paid users experience unexpected rate limits and occasional outages.

Name a single other major **social network** around today that has an API and allows third-party clients. The only one I can think of is Reddit - and even in that case, there are numerous features already being locked out of third-party clients. They are on the same path as Twitter, and at some point they will realize that maintaining a gigantic cost center that provides no revenue (since they don't control ads) and does not allow them to rapidly innovate or build a brand (since they don't control the app) does not make a lot of business sense.

The death of the Twitter API is long, long overdue. Bad for us consumers? Sure. But these companies are not charities, they exist to make money.

Given his heavy investment into XAI, Elon Musk should support AI Agentic Workflows which interact with X through selenium/puppeteer. Otherwise, he'd be anti-AI and threaten US digital sovereignty and national security.

<!-- ### my workflow prioritizes:

1. **Insight Grading**: The system grades tweets based on their insightfulness. Insight is determined by analyzing the content of the tweet, considering factors such as relevance, originality, and depth of information. The grading process involves:
   - **Relevance**: How closely the tweet relates to the specified topic or trend.
   - **Originality**: The uniqueness of the information or perspective provided in the tweet.
   - **Depth**: The level of detail and thoroughness in the tweet's content.

2. **Automated Analysis**: The agents use natural language processing (NLP) techniques to evaluate the tweets. This includes sentiment analysis, keyword extraction, and contextual understanding to score the tweets accurately.

3. **Scoring System**: Each tweet is assigned a score based on the combined metrics of relevance, originality, and depth. Higher scores indicate more insightful tweets, which are prioritized for responses and retweets.

4. **Continuous Improvement**: The grading algorithm is continuously refined based on feedback and new data, ensuring that the system adapts to changing trends and improves its accuracy over time. -->

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

3. Set up configuration and Twitter authentication:
   - Copy `config.json` and customize the cookie file path if needed
   - Create a `cookies.json` file (or use the path specified in config.json)
   - Format the cookies file as shown below:
   ```json
   [
     {
       "name": "auth_token",
       "value": "YOUR_AUTH_TOKEN_HERE",
       "domain": ".x.com",
       "path": "/",
       "secure": true,
       "httpOnly": true,
       "sameSite": "Lax"
     },
     {
       "name": "ct0",
       "value": "YOUR_CT0_TOKEN_HERE",
       "domain": ".x.com",
       "path": "/",
       "secure": true,
       "httpOnly": false,
       "sameSite": "Lax"
     }
   ]
   ```
   - You can obtain these cookies by logging into Twitter in your browser and extracting them using browser developer tools
   - See `cookies.example.json` for a complete example



## Key Components

### Workflow Scripts
- **tweet-finder_workflow.py**: Monitors Twitter lists for new tweets and fetches their details.
- **reply-draft_workflow.py**: Generates AI-powered reply options for tweets and posts selected replies.
- **setup-new-account_workflow.py**: Automates initial account setup (following/blocking users, creating lists).
- **x_follower_automation.py**: Automates following users who are followers of a target account.
- **persona_tweet_workflow.py**: Automates posting tweets with persona integration.

### Twitter API Modules
- **get_tweet (get tweet w/ id)**: Fetches and parses tweet details.
- **manage_posts (create/reply to posts)**: Creates new posts and replies to existing tweets.
- **follows (follow user)**: Manages user following.
- **blocks (block user)**: Manages user blocking.
- **lists (create list, add list members, get list post timeline)**: Creates and manages Twitter lists.
- **persona_manager**: Manages persona data for tweet generation.
- **tweet_generator**: Generates tweets with persona integration.


## Data Structure
The toolkit stores data in JSON files in the data directory:

- **000_about_me.json**: User account information
- **001_saved_tweets.json**: Tweets fetched from Twitter
- **002_generated_tweets.json**: AI-generated reply options
- **003_posted_tweets.json**: Record of posted tweets/replies
- **004_users.json**: User information for following/blocking
- **005_lists.json**: Twitter list information
- **personas/**: Persona data for tweet generation


## Available Workflows

### X.com Follower Automation
Automates the process of following users who are followers of a specified target account. See [X_FOLLOWER_AUTOMATION.md](X_FOLLOWER_AUTOMATION.md) for detailed instructions.

```bash
# Example usage
python browser-use/x_follower_automation.py --target elonmusk --goal 20 --max-refreshes 10
```

### Persona-Based Tweet Generation
Generates tweets in the voice and style of specific personas, with support for media tweets. See [PERSONA_TWEET_README.md](PERSONA_TWEET_README.md) for detailed instructions.

```bash
# Generate a post with a specific persona
python persona_tweet_example.py --persona personas/holly_snow.json --action post

# Generate a post with random media from the media directory
python persona_tweet_example.py --persona personas/holly_snow.json --action post --random-media

# Run timeline monitoring with persona integration and random media
python -m browser_use.my_twitter_api_v3.persona_tweet_workflow --persona personas/holly_snow.json --action monitor --interval 1800 --max-posts 10 --random-media
```

# Roadmap
- [ ] Specification for users with Twitter Premium. More cost effective to use twitter decks (pro.x.com/i/decks/[id]) given less UI clutter.
- [ ] Refactor my_twitter_api folder; all API methods should be one .py file with prompts/browser-use settings modularized
- [ ] If in prod, use a proper database solution
- [ ] Voice AI w/ connection to Twitter Spaces
- [ ] Automate the entire twitter account creation process (including 2FA)
- [ ] Optimize prompts/settings by determining success rate of each

<!---
- [ ] Make tutorial video with Telepath music
---->
