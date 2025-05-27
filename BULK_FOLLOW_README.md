# Twitter Following System

This is the main Twitter following system that handles both single and bulk following operations while respecting Twitter's rate limits.

## Features

- **Rate Limiting**: Respects Twitter's 15 follows/minute and 400 follows/day limits
- **Configurable**: All settings controlled via `config.json`
- **Priority-based**: Follow accounts by priority (high, medium, low)
- **Category filtering**: Follow accounts by category
- **Progress tracking**: Tracks which accounts have been followed
- **Retry logic**: Automatic retries on failures
- **Smart delays**: Configurable delays between follows

## Configuration

### Rate Limits (in config.json)
```json
{
  "following": {
    "accounts_file": "./accounts_to_follow.json",
    "rate_limits": {
      "follows_per_minute": 15,
      "follows_per_day": 400,
      "delay_between_follows": 4
    },
    "retry": {
      "max_attempts": 3,
      "delay_on_error": 10
    }
  }
}
```

### Accounts File Format
The accounts file (`accounts_to_follow.json`) contains:
```json
{
  "accounts": [
    {
      "handle": "elonmusk",
      "priority": "high",
      "category": "tech_leaders",
      "followed": false
    }
  ],
  "metadata": {
    "last_updated": "2024-01-01T00:00:00Z",
    "total_accounts": 10,
    "followed_count": 0,
    "pending_count": 10
  }
}
```

## Usage

### Command Line Interface
```bash
# Show current status
python bulk_follow_workflow.py --strategy status

# Follow high priority accounts (max 5)
python bulk_follow_workflow.py --strategy priority --filter high --max 5

# Follow accounts in tech_leaders category
python bulk_follow_workflow.py --strategy category --filter tech_leaders

# Follow all pending accounts (max 10)
python bulk_follow_workflow.py --strategy all --max 10

# Smart follow (high -> medium -> low priority)
python bulk_follow_workflow.py --strategy smart --max 15

# Dry run (show what would happen)
python bulk_follow_workflow.py --strategy smart --max 5 --dry-run
```

### Programmatic Usage

#### Simple Single Follow
```python
from my_twitter_api_v3.follows.follow_system import follow_user

# Follow a single user (with rate limiting)
success = await follow_user("elonmusk")
print(f"Result: {'Success' if success else 'Failed'}")
```

#### Advanced Usage
```python
from my_twitter_api_v3.follows.follow_system import get_follower

# Get follower instance for more control
follower = get_follower()

# Check current status
status = follower.get_follow_status()
print(status)

# Follow multiple users with rate limiting
users = ["sama", "pmarca", "garrytan"]
for user in users:
    success = await follower.follow_user(user)
    print(f"@{user}: {'Success' if success else 'Failed'}")
```

## Account Management

### Adding New Accounts
Edit `accounts_to_follow.json`:
```json
{
  "handle": "new_account",
  "priority": "medium",
  "category": "news",
  "followed": false
}
```

### Priority Levels
- **high**: Most important accounts (followed first)
- **medium**: Moderately important accounts
- **low**: Least important accounts (followed last)

### Categories
You can create any categories you want:
- `tech_leaders`
- `ai_ml`
- `news`
- `entertainment`
- `sports`
- etc.

## Rate Limiting Details

### Twitter's Limits
- **15 follows per minute** (rolling window)
- **400 follows per day** (resets at midnight)

### System Behavior
- Automatically waits when minute limit is reached
- Stops when daily limit is reached
- Configurable delays between follows (default: 4 seconds)
- Tracks limits across sessions

### Customizing Limits
You can adjust limits in `config.json` if you have different account limits:
```json
{
  "following": {
    "rate_limits": {
      "follows_per_minute": 10,  // Lower for safety
      "follows_per_day": 300,    // Conservative limit
      "delay_between_follows": 6  // Longer delays
    }
  }
}
```

## Error Handling

### Automatic Retries
- Failed follows are retried up to 3 times (configurable)
- 10-second delay between retry attempts (configurable)
- Detailed error logging

### Common Issues
1. **Rate limits exceeded**: System automatically waits
2. **Account not found**: Marked as failed, continues with next
3. **Already following**: Marked as success
4. **Network errors**: Retried automatically

## Monitoring Progress

### Status Command
```bash
python bulk_follow_workflow.py --strategy status
```

Shows:
- Total accounts vs followed vs pending
- Current rate limit status
- Configuration settings

### Log Output
The system provides detailed logging:
```
Following @elonmusk (Priority: high, Category: tech_leaders)...
✓ Successfully followed @elonmusk
Rate limit status: 1/400 daily, 1/15 per minute
```

## Best Practices

1. **Start Small**: Test with a few accounts first
2. **Use Priorities**: Set important accounts to "high" priority
3. **Monitor Limits**: Check status regularly
4. **Spread Sessions**: Don't try to follow 400 accounts at once
5. **Update Regularly**: Keep your accounts list current

## File Structure
```
twagent/
├── config.json                           # Main configuration
├── accounts_to_follow.json               # Accounts to follow
├── browser-use/
│   ├── bulk_follow_workflow.py          # CLI interface
│   └── my_twitter_api_v3/
│       └── follows/
│           ├── bulk_follow.py           # Core bulk follow logic
│           └── follow_user.py           # Single user follow (legacy)
```
