import os
import re
from typing import Optional
from urllib.parse import urlparse

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


nitter_rt_pattern = r'^RT by @[\w\d_]+:(.*)'


def fix_nitter_rt_title(title: str) -> str:
    match = re.match(nitter_rt_pattern, title, re.DOTALL)
    if match:
        content = match.group(1)
        return content.lstrip()
    return title


def fix_nitter_urls_in_text(text: str) -> str:
    nitter_base_url = get_nitter_base_url()
    nitter_hostname = urlparse(nitter_base_url).netloc
    return text.replace(nitter_hostname, "twitter.com")


def create_nitter_feed_url(twitter_handle: str) -> str:
    return f"{get_nitter_base_url()}/{twitter_handle}/rss?key={get_nitter_rss_password()}"


def extract_twitter_handle_from_feed_url(url: str) -> Optional[str]:
    nitter_base_url = get_nitter_base_url()
    if not url.startswith(nitter_base_url):
        return None
    return url[len(nitter_base_url):].split('/')[1]


twitter_domains = {
    "twitter.com",
    "mobile.twitter.com",
    "x.com",
    "mobile.x.com",
    "fxtwitter.com",
    "fixupx.com"
}


def extract_twitter_handle_from_url(url: str) -> Optional[str]:
    if urlparse(url).netloc not in twitter_domains:
        return None
    
    path = urlparse(url).path
    if path.startswith('/'):
        path = path[1:]
    
    handle = path.split('/')[0]
    if handle:
        return handle
    return None


def fix_shareable_twitter_url(url: str) -> str:
    for domain in twitter_domains:
        if url.startswith(f'http://{domain}'):
            return url.replace(f'http://{domain}', 'https://fxtwitter.com')
        elif url.startswith(f'https://{domain}'):
            return url.replace(f'https://{domain}', 'https://fxtwitter.com')
    return url
