# Twitter Follower Automation

This script automates the process of following users from a target account's followers list. It uses the browser-use package to control the browser and interact with Twitter.

## Features

- **Target-based Following**: Follow users who follow a specific target account
- **Configurable Goals**: Set a specific number of users to follow
- **Safety Limits**: Maximum page refreshes and follow rate limits
- **Error Handling**: Robust error handling and recovery
- **Detailed Reporting**: Comprehensive results tracking and reporting
- **Rate Limiting**: Configurable delays between actions to avoid detection

## Usage

### Command Line Interface

```bash
python twitter_follower_automation.py elonmusk --goal 20 --max-refreshes 10 --delay 3 --batch-size 15
```

### Parameters

- `username`: Target username whose followers you want to follow (required)
- `--goal`: Number of users to follow (default: 10)
- `--max-refreshes`: Maximum number of page refreshes (default: 10)
- `--delay`: Delay between follows in seconds (default: 2.5)
- `--batch-size`: Number of follows per batch before scrolling (default: 20)

### Results

The script saves detailed results to a JSON file in the `results` directory:

```json
{
  "target_username": "elonmusk",
  "follow_goal": 20,
  "follows_completed": 18,
  "refreshes_done": 3,
  "time_taken": "0:05:23.456789",
  "status": "Goal Reached",
  "errors": []
}
```

## How It Works

The automation follows a structured workflow:

### Phase 1: Navigate to Target

1. Go to `https://x.com/[TARGET_USERNAME]/followers`
2. Wait for the page to load completely
3. Verify the correct URL is loaded

### Phase 2: Process Current Follower List

1. **Identify Follow Buttons:**
   - Look for buttons with text "Follow" (white text on black button)
   - Ignore buttons that say "Following" (already following)
   - Ignore buttons that say "Pending" (request sent)

2. **Execute Follows:**
   - Click each "Follow" button found on current view
   - Wait 2-3 seconds after each click
   - Count each successful follow
   - If follow count reaches goal → Complete

3. **Load More Followers:**
   - Scroll down to bottom of page
   - Wait 4 seconds for new followers to load
   - If new "Follow" buttons appear → Return to step 1
   - If no new content loads → Go to Phase 3

### Phase 3: Refresh for New Followers

1. **Refresh Strategy:**
   - Refresh the page
   - Wait 5 seconds for page reload
   - Verify still on followers page
   - Return to Phase 2, step 1

2. **Refresh Limit:**
   - Track number of refreshes
   - If refresh count reaches max limit → Complete

### Phase 4: Complete and Report

1. **Stop Conditions:**
   - Follow goal reached, OR
   - Max refreshes reached, OR
   - No more "Follow" buttons found after 3 consecutive refreshes

2. **Report Results:**
   - Total new follows completed
   - Total page refreshes
   - Time taken
   - Final status

## Safety & Rate Limiting

- **Delays:** Minimum 2 seconds between follows
- **Batch Size:** Process maximum 20 follows per page before scrolling
- **Error Handling:** If any follow fails, wait 10 seconds before continuing
- **Detection Avoidance:** Vary delay times between 2-4 seconds randomly

## Stopping Triggers

- Immediately stop if you see any error messages
- Stop if follow buttons become unclickable
- Stop if redirected away from followers page
- Stop if browser shows any security warnings

## Integration with Twitter API

This script integrates with the refactored Twitter API module, using the `TwitterBrowserSession` class for browser session management and the `get_twitter_config` function for configuration.

## Customization

You can customize the automation by modifying the `FollowerAutomation` class:

```python
automation = FollowerAutomation(
    target_username="elonmusk",
    follow_goal=20,
    max_refreshes=10,
    delay_between_follows=2.5,
    delay_after_error=10.0,
    batch_size=20
)

results = await automation.run()
```

