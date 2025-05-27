# Twikit Follower Module

This module allows you to automatically follow users who are followers of specified target accounts using the Twikit library. It provides a more efficient way to grow your Twitter following by targeting users who are already interested in similar content.

## Features

- Collect followers from specified target accounts
- Apply filters to find quality accounts to follow
- Follow users with rate limiting to avoid Twitter restrictions
- Command-line interface for easy management
- Cookie-based authentication using your existing Twitter session

## Setup

1. Make sure you have the required dependencies installed:
   ```
   pip install twikit
   ```

2. Configure your Twitter cookies in the `cookies.json` file (see `cookies.example.json` for format)

3. Set up your target accounts in `target_accounts.json` or use the CLI to add targets

## Usage

### Command Line Interface

The module provides a command-line interface through `twikit_follow_workflow.py`:

```bash
# Show current status
python twikit_follow_workflow.py --status

# Collect users to follow without following them
python twikit_follow_workflow.py --collect

# Follow collected users (up to 50)
python twikit_follow_workflow.py --follow --max 50

# Run the full workflow (collect and follow)
python twikit_follow_workflow.py --run --max 100

# Add a new target account
python twikit_follow_workflow.py --target elonmusk

# List all target accounts
python twikit_follow_workflow.py --list-targets

# Remove a target account
python twikit_follow_workflow.py --remove-target elonmusk
```

### Target Accounts Configuration

The `target_accounts.json` file contains the list of accounts to get followers from:

```json
{
  "targets": [
    {
      "handle": "elonmusk",
      "max_followers": 100,
      "min_followers_count": 10,
      "max_following_count": 5000,
      "verified_only": false
    },
    {
      "handle": "OpenAI",
      "max_followers": 100,
      "min_followers_count": 10,
      "max_following_count": 5000,
      "verified_only": false
    }
  ]
}
```

Parameters for each target:
- `handle`: Twitter handle (without @)
- `max_followers`: Maximum number of followers to collect from this account
- `min_followers_count`: Minimum followers a user should have to be considered
- `max_following_count`: Maximum following count to avoid spam accounts
- `verified_only`: Whether to only follow verified accounts

## Rate Limiting

The module implements rate limiting to avoid Twitter restrictions:
- Follows per minute: Configurable in `config.json` (default: 15)
- Follows per day: Configurable in `config.json` (default: 400)
- Delay between follows: Configurable in `config.json` (default: 4 seconds with random jitter)

## Integration with Existing Code

You can also use the module programmatically in your Python code:

```python
import asyncio
from browser_use.my_twitter_api_v3.follows.twikit_follower import get_twikit_follower

async def example():
    # Get the follower instance
    follower = get_twikit_follower()
    
    # Initialize the client
    await follower.initialize_client()
    
    # Collect users to follow
    await follower.collect_users_to_follow()
    
    # Follow up to 50 users
    results = await follower.follow_collected_users(max_users=50)
    print(f"Followed: {results['followed']}, Failed: {results['failed']}")

# Run the example
asyncio.run(example())
```

## How It Works

1. The module uses Twikit to authenticate with Twitter using your cookies
2. It fetches followers from each target account
3. It applies filters to find quality accounts to follow
4. It follows users with rate limiting to avoid Twitter restrictions

## Troubleshooting

- **Authentication Issues**: Make sure your cookies are valid and up-to-date in `cookies.json`
- **Rate Limiting**: If you hit Twitter's rate limits, the module will pause automatically
- **Account Restrictions**: If your account is restricted by Twitter, you may need to wait before using the module again

