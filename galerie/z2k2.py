import os
from typing import Dict
import requests


def get_z2k2_base_url() -> str:
    """Get z2k2 base URL from environment variable."""
    if 'Z2K2_BASE_URL' not in os.environ:
        raise ValueError("Z2K2_BASE_URL environment variable is not set.")
    base_url = os.environ['Z2K2_BASE_URL']
    if base_url.endswith('/'):
        base_url = base_url[:-1]
    return base_url


def get_twitter_user_status(handle: str) -> Dict[str, bool]:
    """
    Get Twitter user account status from z2k2 API.

    Args:
        handle: Twitter username without @

    Returns:
        Dictionary with status flags:
        - 'absent': True if user doesn't exist
        - 'protected': Boolean (if user exists)
        - 'suspended': Boolean (if user exists)

    Raises:
        requests.HTTPError: For API errors (404, 429, 500, 502)
        ValueError: If Z2K2_BASE_URL is not set
    """
    base_url = get_z2k2_base_url()
    url = f"{base_url}/twitter/profile/{handle}/_status"

    response = requests.get(url)
    response.raise_for_status()
    return response.json()
