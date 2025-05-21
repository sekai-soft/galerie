import os
from typing import Optional


def get_nitter_base_url():
    if 'NITTER_BASE_URL' not in os.environ:
        raise ValueError("NITTER_BASE_URL environment variable is not set.")
    nitter_base_url = os.environ['NITTER_BASE_URL']
    if nitter_base_url.endswith('/'):
        nitter_base_url = nitter_base_url[:-1]
    return nitter_base_url


def get_nitter_rss_password():
    if 'NITTER_RSS_PASSWORD' not in os.environ:
        raise ValueError("NITTER_RSS_PASSWORD environment variable is not set.")
    return os.environ['NITTER_RSS_PASSWORD']


def fix_nitter_url(url: str) -> str:
    return url.replace(get_nitter_base_url(), "https://twitter.com")


def get_nitter_feed_url(twitter_handle: str) -> str:
    return f"{get_nitter_base_url()}/@{twitter_handle}/rss?key={get_nitter_rss_password()}"


def parse_twitter_handle(feed_url: str) -> Optional[str]:
    nitter_base_url = get_nitter_base_url()
    if not feed_url.startswith(nitter_base_url):
        return None
    return feed_url[len(nitter_base_url):].split('/')[1]
