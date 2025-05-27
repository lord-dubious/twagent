"""
Centralized cookie management for Twitter API v3
Handles loading cookies from configurable JSON file location
"""

import json
import os
import pathlib
from typing import List, Dict, Any, Optional
from browser_use.browser.context import BrowserContextConfig


class CookieManager:
    """Manages Twitter cookies with configurable file location"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize cookie manager with config file
        
        Args:
            config_path: Path to config.json file. If None, searches for it automatically.
        """
        self.config = self._load_config(config_path)
        self.cookie_file_path = self._resolve_cookie_path()
    
    def _load_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """Load configuration from config.json"""
        if config_path is None:
            # Search for config.json starting from current file location
            current_dir = pathlib.Path(__file__).parent
            
            # Try different locations
            possible_paths = [
                current_dir / "../../../../config.json",  # From utils/ to project root
                current_dir / "../../../config.json",    # Alternative path
                current_dir / "../../config.json",       # Another alternative
                pathlib.Path.cwd() / "config.json",      # Current working directory
            ]
            
            for path in possible_paths:
                if path.exists():
                    config_path = str(path.resolve())
                    break
            else:
                raise FileNotFoundError(
                    "config.json not found. Please ensure it exists in the project root or provide config_path parameter."
                )
        
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            raise Exception(f"Error loading config from {config_path}: {e}")
    
    def _resolve_cookie_path(self) -> str:
        """Resolve the absolute path to the cookie file"""
        cookie_path = self.config.get("cookies", {}).get("file_path", "./cookies.json")
        
        # If relative path, make it relative to config file location
        if not os.path.isabs(cookie_path):
            config_dir = pathlib.Path(__file__).parent / "../../../../"
            cookie_path = str((config_dir / cookie_path).resolve())
        
        return cookie_path
    
    def load_cookies(self) -> List[Dict[str, Any]]:
        """
        Load Twitter cookies from the configured JSON file
        
        Returns:
            List of cookie dictionaries compatible with browser automation
        """
        try:
            with open(self.cookie_file_path, 'r') as f:
                cookies_data = json.load(f)
            
            # Ensure cookies_data is a list
            if not isinstance(cookies_data, list):
                raise ValueError("Cookie file must contain a JSON array of cookie objects")
            
            # Validate and normalize cookie format
            normalized_cookies = []
            for cookie in cookies_data:
                if not isinstance(cookie, dict):
                    continue
                
                # Handle different cookie formats (name/key, value, domain, path)
                normalized_cookie = {
                    "name": cookie.get("name") or cookie.get("key", ""),
                    "value": cookie.get("value", ""),
                    "domain": cookie.get("domain", ".x.com"),
                    "path": cookie.get("path", "/"),
                    "secure": cookie.get("secure", True),
                    "httpOnly": cookie.get("httpOnly", False),
                    "sameSite": cookie.get("sameSite", "Lax")
                }
                
                if normalized_cookie["name"] and normalized_cookie["value"]:
                    normalized_cookies.append(normalized_cookie)
            
            if not normalized_cookies:
                raise ValueError("No valid cookies found in cookie file")
            
            return normalized_cookies
            
        except FileNotFoundError:
            raise FileNotFoundError(
                f"Cookie file not found at {self.cookie_file_path}. "
                f"Please create the file or update the path in config.json"
            )
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in cookie file {self.cookie_file_path}: {e}")
    
    def get_cookie_file_path(self) -> str:
        """Get the path to the cookie file for browser-use compatibility"""
        return self.cookie_file_path
    
    def create_browser_context_config(self, **kwargs) -> BrowserContextConfig:
        """
        Create a BrowserContextConfig with the cookie file path
        
        Args:
            **kwargs: Additional arguments to pass to BrowserContextConfig
        
        Returns:
            BrowserContextConfig instance with cookies configured
        """
        return BrowserContextConfig(
            cookies_file=self.cookie_file_path,
            **kwargs
        )
    
    def get_config(self) -> Dict[str, Any]:
        """Get the full configuration dictionary"""
        return self.config


# Global instance for easy access
_cookie_manager = None


def get_cookie_manager(config_path: Optional[str] = None) -> CookieManager:
    """
    Get the global cookie manager instance
    
    Args:
        config_path: Path to config.json file (only used on first call)
    
    Returns:
        CookieManager instance
    """
    global _cookie_manager
    if _cookie_manager is None:
        _cookie_manager = CookieManager(config_path)
    return _cookie_manager


def load_cookies() -> List[Dict[str, Any]]:
    """
    Convenience function to load cookies using the global cookie manager
    
    Returns:
        List of cookie dictionaries
    """
    return get_cookie_manager().load_cookies()


def get_cookie_file_path() -> str:
    """
    Convenience function to get cookie file path using the global cookie manager
    
    Returns:
        Path to the cookie file
    """
    return get_cookie_manager().get_cookie_file_path()
