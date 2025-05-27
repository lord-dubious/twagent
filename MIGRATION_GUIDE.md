# Migration Guide: Cookie Management Update

This guide explains how to migrate from the old hardcoded `twitter_cookies.txt` system to the new centralized cookie management system.

## What Changed

### Before (Old System)
- Each module had hardcoded paths to `twitter_cookies.txt`
- Cookie file format was inconsistent
- No centralized configuration
- Cookie file location was not configurable

### After (New System)
- Centralized cookie management through `utils/cookie_manager.py`
- Configurable cookie file location via `config.json`
- Consistent JSON format for cookies
- Better error handling and validation

## Migration Steps

### 1. Update Your Cookie File

**Old format** (`twitter_cookies.txt`):
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

**New format** (`cookies.json`):
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

### 2. Create Configuration File

Create `config.json` in the project root:
```json
{
  "cookies": {
    "file_path": "./cookies.json",
    "format": "json"
  },
  "data": {
    "directory": "./data"
  },
  "browser": {
    "headless": false,
    "timeout": 30000
  },
  "api": {
    "openai_model": "gpt-4o-mini-2024-07-18",
    "max_retries": 3
  }
}
```

### 3. Move Your Cookie File

1. Copy your existing `twitter_cookies.txt` content
2. Convert it to the new JSON format (add the additional fields)
3. Save it as `cookies.json` (or the path specified in your config)
4. Delete the old `twitter_cookies.txt` files

### 4. Update Custom Code (If Any)

If you have custom code that loads cookies, update it to use the new cookie manager:

**Old way:**
```python
import json
import pathlib

def load_cookies():
    current_dir = pathlib.Path(__file__).parent
    parent_dir = current_dir.parent
    cookie_path = parent_dir / "twitter_cookies.txt"
    
    with open(cookie_path, "r") as f:
        cookies_data = f.read()
    
    return json.loads(cookies_data)
```

**New way:**
```python
from utils.cookie_manager import load_cookies

# Simple usage
cookies = load_cookies()

# Or get the cookie manager for more control
from utils.cookie_manager import get_cookie_manager

cookie_manager = get_cookie_manager()
cookies = cookie_manager.load_cookies()
cookie_file_path = cookie_manager.get_cookie_file_path()
```

## Configuration Options

### Cookie File Location

You can customize the cookie file location in `config.json`:

```json
{
  "cookies": {
    "file_path": "/path/to/your/cookies.json"
  }
}
```

Supported path formats:
- Relative paths: `"./cookies.json"`, `"../auth/cookies.json"`
- Absolute paths: `"/home/user/cookies.json"`, `"C:\\Users\\User\\cookies.json"`

### Multiple Cookie Files

For different accounts or environments, you can:

1. Use different config files:
```python
from utils.cookie_manager import CookieManager

# Production cookies
prod_manager = CookieManager("config.prod.json")
prod_cookies = prod_manager.load_cookies()

# Development cookies  
dev_manager = CookieManager("config.dev.json")
dev_cookies = dev_manager.load_cookies()
```

2. Or specify the cookie file directly:
```python
from utils.cookie_manager import CookieManager

manager = CookieManager()
# Override the config file path
manager.cookie_file_path = "/path/to/specific/cookies.json"
cookies = manager.load_cookies()
```

## Troubleshooting

### Common Issues

1. **FileNotFoundError: config.json not found**
   - Ensure `config.json` exists in the project root
   - Or provide the config path explicitly: `CookieManager("path/to/config.json")`

2. **FileNotFoundError: Cookie file not found**
   - Check the path in `config.json` is correct
   - Ensure the cookie file exists at the specified location

3. **ValueError: Invalid JSON in cookie file**
   - Validate your JSON syntax
   - Use the example format provided above

4. **Import errors**
   - Ensure you're running from the correct directory
   - Check that the `utils` package is in the Python path

### Validation

Test your setup:
```python
from utils.cookie_manager import get_cookie_manager

try:
    manager = get_cookie_manager()
    cookies = manager.load_cookies()
    print(f"Successfully loaded {len(cookies)} cookies")
    print(f"Cookie file: {manager.get_cookie_file_path()}")
except Exception as e:
    print(f"Error: {e}")
```

## Benefits of the New System

1. **Centralized Management**: All cookie handling in one place
2. **Configurable**: Easy to change cookie file location
3. **Better Error Handling**: Clear error messages and validation
4. **Consistent Format**: Standardized cookie structure
5. **Future-Proof**: Easy to extend with new features
6. **Multiple Environments**: Support for different configurations

## Backward Compatibility

The new system is **not** backward compatible with the old `twitter_cookies.txt` files. You must migrate your cookie files to the new JSON format and update your configuration.

However, the migration is straightforward and only needs to be done once.
