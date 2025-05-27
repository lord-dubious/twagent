"""
Legacy follow_user module - now uses the main following system
"""

import asyncio

from .follow_system import follow_user as _follow_user


async def follow_user(handle="@doge"):
    """
    Follow a single user using the main following system with rate limiting

    Args:
        handle: Twitter handle to follow (with or without @)

    Returns:
        bool: True if successful, False otherwise
    """
    return await _follow_user(handle)


if __name__ == "__main__":
    asyncio.run(follow_user())
