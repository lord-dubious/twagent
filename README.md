# Project Overview

This repository leverages AI agents (w/ `browser_use`, `elevenlabs`) to monitor twitter accounts, analyze trends, score tweets, reply/post/retweet, and speak in twitter spaces.

## AI Agentic Workflow Structure

The workflow is designed for pseudosatirical social causes. It aims to create provocative arguments and pick fights online.

<!-- 1) **What people should know (mission statement; system prompt)**
  ```
  [{
    "cause": "The Bureau of Ergonomic Justice And Reparations"
    "description": "Advocating for the fair distribution of standing desks, 
                    lumbar-support chairs, 
                    and those squishy keyboard wrist pads."
  }]
```
2) **Accounts and Trends to monitor**
  specify how much they would support the mission statement (20 is agreement, -20 is oppose)
```
//accounts
[
  {
    "handle": "@HealthyPostureAlliance",
    "rating": 20
  },
  {
    "handle": "@BendAtTheKneesOrHips",
    "rating": 8
  },
  {
    "handle": "@BringBackCubicles",
    "rating": -20
  }
  ...
]
```
```
//trends
[
  {
    "handle": "#ErgonomicRevolution",
    "rating": 18
  },
  {
    "handle": "#OfficePostureMatters",
    "rating": 10
  },
  {
    "handle": "#SittingIsFreedom",
    "rating": -20
  }
  ...
]
``` -->


## Why browser-use? Why not just use Twitter's V2 API?

This approach was chosen as a solution because the Twitter API is prohibitively expensive and is often seen as anti-developer. 

- **Frequent API Changes**: Pricing, access levels, and endpoints have changed unpredictably. Some previously available endpoints have been removed or moved to higher-cost tiers.
- **Expensive Paid Tiers**: Free-tier access is very limited, and paid tiers are costly.
- **Rate Limits & Downtime**: Even paid users experience unexpected rate limits and occasional outages.

Name a single other major **social network** around today that has an API and allows third-party clients. The only one I can think of is Reddit - and even in that case, there are numerous features already being locked out of third-party clients. They are on the same path as Twitter, and at some point they will realize that maintaining a gigantic cost center that provides no revenue (since they don't control ads) and does not allow them to rapidly innovate or build a brand (since they don't control the app) does not make a lot of business sense.

The death of the Twitter API is long, long overdue. Bad for us consumers? Sure. But these companies are not charities, they exist to make money.

Given his heavy investment into XAI, Elon Musk should support AI Agentic Workflows which interact with X through selenium/puppeteer. Otherwise, he'd be anti-AI and threaten US digital sovereignty and national security.


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