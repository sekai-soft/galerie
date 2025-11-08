import os
from typing import Dict
import requests


def get_z2k2_base_url() -> str:
    if 'Z2K2_BASE_URL' not in os.environ:
        raise ValueError("Z2K2_BASE_URL environment variable is not set.")
    base_url = os.environ['Z2K2_BASE_URL']
    if base_url.endswith('/'):
        base_url = base_url[:-1]
    return base_url


def get_twitter_user_status(handle: str) -> Dict[str, bool]:
    base_url = get_z2k2_base_url()
    url = f"{base_url}/twitter/profile/{handle}/_status"

    response = requests.get(url)
    response.raise_for_status()
    return response.json()
