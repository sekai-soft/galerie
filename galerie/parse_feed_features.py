import re
from typing import Dict, Optional, Tuple
from urllib.parse import unquote_plus, urlparse, parse_qs

nitter_on_fly_pattern = re.compile(r'https://nitter-[^.]+\.fly\.dev/([^/]+)/rss')

def is_nitter_on_fly(feed_url: str) -> bool:
    return nitter_on_fly_pattern.match(feed_url) is not None

def extract_nitter_on_fly(feed_url: str) -> Tuple[str, str]:
    parsed_url = urlparse(feed_url)
    domain = parsed_url.netloc
    query_params = parse_qs(parsed_url.query)
    password = query_params['key'][0]
    return (domain, password)

def parse_twitter_handle(feed_url: str) -> Optional[str]:
    match = nitter_on_fly_pattern.search(feed_url)
    if not match:
        return None
    return match.group(1)

def parse_feature_twitter(features: Dict):
    twitter_handle = parse_twitter_handle(features["feed_url"])
    if twitter_handle:
        features["twitter_handle"] = twitter_handle

def parse_feature_rss_lambda(features: Dict):
    feed_url = features["feed_url"]
    if feed_url.startswith("https://rss-lambda.xyz"):
        parsed_feed_url = urlparse(feed_url)
        parsed_qs = parse_qs(parsed_feed_url.query)
        features["feed_url"] = unquote_plus(parsed_qs["url"][0])
        if parsed_feed_url.path == "/to_image_feed":
            features["rss_lambda_to_image_feed"] = True
        elif parsed_feed_url.path == "/rss_image_recog":
            if parsed_qs["class_id"][0] == "0":
                features["rss_lambda_image_recog_human"] = True
            features["rss_lambda_image_recog"] = True
        elif parsed_feed_url.path == "/rss":
            features["rss_lambda_image_simple_filters"] = True
            if parsed_qs.get("param"):
                features["rss_lambda_image_simple_filters_param"] = parsed_qs["param"]
        parse_feature_rss_lambda(features)
    else:
        parse_feature_twitter(features)

def parse_feed_features(feed_url: str) -> Dict:
    features = {
        "feed_url": unquote_plus(feed_url)
    }
    parse_feature_rss_lambda(features)
    return features
