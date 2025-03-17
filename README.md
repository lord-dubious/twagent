# Project Overview

This repository leverages AI agents (w/ `browser_use`, `elevenlabs`) to monitor twitter accounts, analyze trends, score tweets, and reply/post/retweet.

### My Workers
- **Agent A**: Continuously monitor a specified list of accounts and save latest posts/replies database

- **Agent B1**: Monitor the [Trending](https://x.com/explore/tabs/keyword) and [News](https://x.com/explore/tabs/news) tabs by adjusting the location settings, select relevant trends, save their links and descriptions.

- **Agent B2**: Go through the relevant trends, determine which posts to respond to, save those posts.

- **Agent C** (not browser-base): score all the current tweets in the past 10 minutes, determine which ones to respond to.

- **Agent D**: Craft replies/posts, score these.

- **Agent E**: Respond to the highest-scoring tweets. Retweet those. The max tweet count is 2,400 per day.

- **Agent F**: Stream with Elevenlabs to OBS and say them in a twitter space. 


## A. Why this approach? Why not just use Twitter's V2 API?

This approach was chosen as a solution because the Twitter API is prohibitively expensive and is often seen as anti-developer. 

- **Frequent API Changes**: Pricing, access levels, and endpoints have changed unpredictably. Some previously available endpoints have been removed or moved to higher-cost tiers.
- **Expensive Paid Tiers**: Free-tier access is very limited, and paid tiers are costly.
- **Rate Limits & Downtime**: Even paid users experience unexpected rate limits and occasional outages.

Name a single other major social network around today that has an API and allows third-party clients. The only one I can think of is Reddit - and even in that case, there are numerous features already being locked out of third-party clients. They are on the same path as Twitter, and at some point they will realize that maintaining a gigantic cost center that provides no revenue (since they don't control ads) and does not allow them to rapidly innovate or build a brand (since they don't control the app) does not make a lot of business sense.

The death of the Twitter API is long, long overdue. Bad for us consumers? Sure. But these companies are not charities, they exist to make money.

Given his heavy investment into XAI, Elon Musk should support AI Agentic Workflows which interact with X through selenium/puppeteer. Otherwise, he'd be anti-AI and threaten US digital sovereignty and national security.


### scraping vs limited/expensive APIs
- Agent A, B1/2 E could be done easily with V2 access, though you'd be rate-limited. Trends API is more unstable with conflicting information in the documentation.
- For X's Communities' feature, you can only do one call per 15 minutes. That is a complete mess and scraping is likely better.

### my workflow prioritizes:

1. **Insight Grading**: The system grades tweets based on their insightfulness. Insight is determined by analyzing the content of the tweet, considering factors such as relevance, originality, and depth of information. The grading process involves:
   - **Relevance**: How closely the tweet relates to the specified topic or trend.
   - **Originality**: The uniqueness of the information or perspective provided in the tweet.
   - **Depth**: The level of detail and thoroughness in the tweet's content.

2. **Automated Analysis**: The agents use natural language processing (NLP) techniques to evaluate the tweets. This includes sentiment analysis, keyword extraction, and contextual understanding to score the tweets accurately.

3. **Scoring System**: Each tweet is assigned a score based on the combined metrics of relevance, originality, and depth. Higher scores indicate more insightful tweets, which are prioritized for responses and retweets.

4. **Continuous Improvement**: The grading algorithm is continuously refined based on feedback and new data, ensuring that the system adapts to changing trends and improves its accuracy over time.

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