import os
from typing import Dict, List
import requests


def get_eyeris_base_url() -> str:
    if 'EYERIS_BASE_URL' not in os.environ:
        raise ValueError("EYERIS_BASE_URL environment variable is not set.")
    base_url = os.environ['EYERIS_BASE_URL']
    if base_url.endswith('/'):
        base_url = base_url[:-1]
    return base_url


def ingest_profile_images(profile_id: str, image_urls: List[str]) -> Dict[str, str]:
    base_url = get_eyeris_base_url()
    url = f"{base_url}/profile/{profile_id}/ingest"

    payload = {
        'image_urls': image_urls
    }

    response = requests.post(url, json=payload)
    response.raise_for_status()
    return response.json()
