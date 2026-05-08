import os
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse


TWITTER_VIDEO_CDN_URL = "https://video.twimg.com/"
TWITTER_MEDIA_CDN_URL = "https://pbs.twimg.com/"


def get_nitter_base_url():
    if 'NITTER_BASE_URL' not in os.environ:
        raise ValueError("NITTER_BASE_URL environment variable is not set.")
    nitter_base_url = os.environ['NITTER_BASE_URL']
    if nitter_base_url.endswith('/'):
        nitter_base_url = nitter_base_url[:-1]
    return nitter_base_url


def is_nitter_url(url: str) -> bool:
    return url.startswith(get_nitter_base_url())


def fix_nitter_url(url: str) -> str:
    return url.replace(get_nitter_base_url(), "https://twitter.com")


nitter_rt_title_pattern = r'^RT(?: by)? @[\w\d_]+:(.*)'


def fix_nitter_rt_title(title: str) -> str:
    match = re.match(nitter_rt_title_pattern, title, re.DOTALL)
    if match:
        content = match.group(1)
        return content.lstrip()
    return title


def fix_nitter_urls_in_text(text: str) -> str:
    nitter_base_url = get_nitter_base_url()
    nitter_hostname = urlparse(nitter_base_url).netloc
    return text.replace(nitter_hostname, "twitter.com")


nitter_rt_text_pattern = r'RT @[\w\d_]+ :\s*(.*)'


def fix_nitter_rt_in_text(text: str) -> str:
    match = re.match(nitter_rt_text_pattern, text, re.DOTALL)
    if match:
        content = match.group(1)
        return content.lstrip()
    return text


def fix_nitter_feed_title(feed_title: str) -> str:
    return feed_title.rsplit(' / ', 1)[0]


def create_nitter_feed_url(twitter_handle: str) -> str:
    rss_password = os.environ.get('NITTER_RSS_PASSWORD')
    if not rss_password:
        return f"{get_nitter_base_url()}/{twitter_handle}/rss"
    return f"{get_nitter_base_url()}/{twitter_handle}/rss?key={rss_password}"


def extract_twitter_handle_from_nitter_feed_url(feed_url: str) -> str | None:
    nitter_base_url = get_nitter_base_url()
    if not feed_url.startswith(nitter_base_url):
        return None
    path = feed_url[len(nitter_base_url):].lstrip('/')
    return path.split('/rss')[0]


twitter_domains = {
    "twitter.com",
    "mobile.twitter.com",
    "x.com",
    "mobile.x.com",
    "fxtwitter.com",
    "fixupx.com"
}


def extract_twitter_handle_from_url(url: str) -> str | None:
    nitter_base_url = get_nitter_base_url()
    if url.startswith(nitter_base_url):
        return url[len(nitter_base_url):].split('/')[1].lower()

    if urlparse(url).netloc not in twitter_domains:
        return None
    
    path = urlparse(url).path
    if path.startswith('/'):
        path = path[1:]
    
    handle = path.split('/')[0]
    if handle:
        return handle.lower()
    return None


def fix_shareable_twitter_url(url: str) -> str:
    for domain in twitter_domains:
        if url.startswith(f'http://{domain}'):
            return url.replace(f'http://{domain}', 'https://fxtwitter.com')
        elif url.startswith(f'https://{domain}'):
            return url.replace(f'https://{domain}', 'https://fxtwitter.com')
    return url


def check_twitter_handle_status(twitter_handle: str) -> str:
    nitter_url = f'{get_nitter_base_url()}/{twitter_handle}'
    resp = str(requests.get(nitter_url).content)
    if twitter_handle not in resp:
        return ''
    if 'not found' in resp:
        return 'absent'
    if 'suspended' in resp:
        return 'suspended'
    if 'tweets are protected' in resp:
        return 'protected'
    return ''


def get_twitter_handle_from_status_url(url: str) -> str:
    status_id = urlparse(url).path.split('/')[-1]
    nitter_url = f'{get_nitter_base_url()}/i/status/{status_id}'
    resp = str(requests.get(nitter_url).content)
    soup = BeautifulSoup(resp, "html.parser")
    main_tweet = soup.find("div", class_="main-tweet")
    return main_tweet.find(attrs={"data-username": True})["data-username"]
