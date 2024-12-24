import re
from typing import Dict
from urllib.parse import unquote

def parse_feature_twitter(feed_url: str, features: Dict):
    pattern = re.compile(r'https://nitter-[^.]+\.fly\.dev/([^/]+)/rss')
    match = pattern.search(feed_url)
    if match:
        twitter_handle = match.group(1)
        features["twitter_handle"] = twitter_handle

def parse_rss_lambda(feed_url: str, features: Dict):
    if feed_url.startswith("https://rss-lambda.xyz/to_image_feed"):
        url = unquote(feed_url.split("?url=")[1])
        features.update({
            "feed_url": url,
            "rss_lambda_to_image_feed": True
        })
        parse_rss_lambda(url, features)
        return
    parse_feature_twitter(feed_url, features)

def parse_feed_features(feed_url: str) -> Dict:
    features = {}
    parse_rss_lambda(feed_url, features)
    return features
