import os
import base64
import json
from typing import Optional
from flask import request
from galerie.rss_aggregator import RssAggregator
from galerie.fever_aggregator import FeverAggregator
from galerie.miniflux_aggregator import MinifluxAggregator

def try_get_miniflux_aggregator() -> Optional[MinifluxAggregator]:
    env_endpoint = os.getenv('MINIFLUX_ENDPOINT')
    env_username = os.getenv('MINIFLUX_USERNAME')
    env_password = os.getenv('MINIFLUX_PASSWORD')
    if env_endpoint and env_username and env_password:
        return MinifluxAggregator(env_endpoint, env_username, env_password, False)
    return None


def try_get_fever_aggregator(
        logging_in_endpoint: Optional[str] = None,
        logging_in_username: Optional[str] = None,
        logging_in_password: Optional[str] = None) -> Optional[FeverAggregator]:
    env_endpoint = os.getenv('FEVER_ENDPOINT')
    env_username = os.getenv('FEVER_USERNAME')
    env_password = os.getenv('FEVER_PASSWORD')
    if env_endpoint and env_username and env_password:
        return FeverAggregator(env_endpoint, env_username, env_password, False)

    if logging_in_endpoint and logging_in_username is not None and logging_in_password is not None:
        return FeverAggregator(logging_in_endpoint, logging_in_username, logging_in_password, True)

    auth_cookie = request.cookies.get('auth')
    if not auth_cookie:
        return None
    auth = base64.b64decode(auth_cookie).decode('utf-8')
    auth = json.loads(auth)
    cookie_endpoint = auth.get('endpoint')
    cookie_username = auth.get('username')
    cookie_password = auth.get('password')
    if cookie_endpoint and cookie_username and cookie_password:
        return FeverAggregator(cookie_endpoint, cookie_username, cookie_password, True)

    return None


def get_aggregator(
    logging_in_endpoint: Optional[str] = None,
    logging_in_username: Optional[str] = None,
    logging_in_password: Optional[str] = None) -> Optional[RssAggregator]:
    aggregator = try_get_miniflux_aggregator()
    if aggregator:
        return aggregator
    return try_get_fever_aggregator(logging_in_endpoint, logging_in_username, logging_in_password)
