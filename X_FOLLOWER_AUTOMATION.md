# X.com Follower Automation

This tool automates the process of following users who are followers of a specified target account on X.com (formerly Twitter). It uses browser automation to navigate to a target user's followers page and follow users.

## Features

- **Target Specific Users**: Follow the followers of any X.com account
- **Customizable Goals**: Set specific follow targets
- **Smart Refreshing**: Automatically refreshes the page to find new followers
- **Detection Avoidance**: Randomized delays and natural browsing patterns
- **Detailed Reporting**: Track progress and results
- **Safety Limits**: Configurable limits to avoid account restrictions

## Setup Parameters

- **Target Username**: The account whose followers you want to follow
- **Follow Goal**: How many new follows to complete
- **Max Page Refreshes**: Safety limit to prevent endless refreshing

## Usage

### Command Line

```bash
# Basic usage
python browser-use/x_follower_automation.py --target elonmusk --goal 20 --max-refreshes 10

# Save results to a JSON file
python browser-use/x_follower_automation.py --target elonmusk --goal 20 --max-refreshes 10 --save-results
```

### Configuration

The tool uses settings from your `config.json` file for safety parameters and rate limits. You can customize these settings:

```json
{
  "following": {
    "safety": {
      "min_delay_between_follows": 2,
      "max_delay_between_follows": 4,
      "page_load_delay": 5,
      "scroll_delay": 4,
      "error_delay": 10,
      "max_follows_per_page": 20
    },
    "rate_limits": {
      "follows_per_minute": 15,
      "follows_per_day": 400
    }
  }
}
```

## How It Works

### Phase 1: Navigate to Target
1. Goes to `https://x.com/[TARGET_USERNAME]`
2. Waits for profile to load
3. Clicks the "Followers" link/number
4. Waits for followers page to fully load
5. Verifies the correct URL

### Phase 2: Process Current Follower List
1. **Identify Follow Buttons**:
   - Looks for buttons with text "Follow" (white text on black button)
   - Ignores buttons that say "Following" (already following)
   - Ignores buttons that say "Pending" (request sent)

2. **Execute Follows**:
   - Clicks each "Follow" button found on current view
   - Waits 2-3 seconds after each click (randomized)
   - Counts each successful follow
   - If follow count reaches goal → Goes to Phase 4 (Complete)

3. **Load More Followers**:
   - Scrolls down to bottom of page
   - Waits for new followers to load
   - If new "Follow" buttons appear → Returns to step 1
   - If no new content loads → Goes to Phase 3

### Phase 3: Refresh for New Followers
1. **Refresh Strategy**:
   - Refreshes the page
   - Waits for page reload
   - Verifies still on followers page
   - Returns to Phase 2, step 1

2. **Refresh Limit**:
   - Tracks number of refreshes
   - If refresh count reaches max limit → Goes to Phase 4

### Phase 4: Complete and Report
1. **Stop Conditions**:
   - Follow goal reached, OR
   - Max refreshes reached, OR
   - No more "Follow" buttons found after 3 consecutive refreshes

2. **Report Results**:
   - Total new follows completed
   - Total page refreshes
   - Time taken
   - Final status

## Safety & Rate Limiting

- **Delays**: Minimum 2 seconds between follows (randomized)
- **Batch Size**: Process maximum 20 follows per page before scrolling
- **Error Handling**: If any follow fails, wait 10 seconds before continuing
- **Detection Avoidance**: Vary delay times between 2-4 seconds randomly

## Stopping Triggers

- Immediately stops if it sees any error messages
- Stops if follow buttons become unclickable
- Stops if redirected away from followers page
- Stops if browser shows any security warnings

## Expected X.com Behavior

- Followers list shows ~20 users initially
- Scrolling loads more in batches
- Some followers may be private accounts
- Follow buttons may temporarily disable after clicking
- Page refresh shows different follower subset (X.com randomizes display)

## Troubleshooting

- **Navigation Errors**: Make sure the target account exists and is public
- **No Follow Buttons**: The account might not have any followers, or you might be rate-limited
- **Slow Performance**: Increase the page load and scroll delay settings
- **Detection Issues**: Increase the min/max delay between follows

