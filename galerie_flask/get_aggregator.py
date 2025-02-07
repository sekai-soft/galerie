import os
import base64
import json
from typing import Optional
from flask import request
from galerie.rss_aggregator import RssAggregator
from galerie.miniflux_aggregator import MinifluxAggregator


def try_get_miniflux_aggregator(
        logging_in_endpoint: Optional[str] = None,
        logging_in_username: Optional[str] = None,
        logging_in_password: Optional[str] = None,
        aggregator_type: Optional[str] = None) -> Optional[MinifluxAggregator]:
    # determine in env
    env_endpoint = os.getenv('MINIFLUX_ENDPOINT')
    env_username = os.getenv('MINIFLUX_USERNAME')
    env_password = os.getenv('MINIFLUX_PASSWORD')
    if env_endpoint and env_username and env_password:
        return MinifluxAggregator(env_endpoint, env_username, env_password, False)
    
    # determine from login form
    if aggregator_type == 'miniflux' and logging_in_endpoint and logging_in_username is not None and logging_in_password is not None:
        return MinifluxAggregator(logging_in_endpoint, logging_in_username, logging_in_password, True)

    # determine from persisted auth
    auth_cookie = request.cookies.get('auth')
    if not auth_cookie:
        return None
    auth = base64.b64decode(auth_cookie).decode('utf-8')
    auth = json.loads(auth)
    cookie_base_url = auth.get('base_url')
    cookie_username = auth.get('username')
    cookie_password = auth.get('password')
    is_miniflux = auth.get('miniflux', False)
    if is_miniflux and cookie_base_url and cookie_username and cookie_password:
        return MinifluxAggregator(cookie_base_url, cookie_username, cookie_password, True)

    return None


def get_aggregator(
    logging_in_endpoint: Optional[str] = None,
    logging_in_username: Optional[str] = None,
    logging_in_password: Optional[str] = None,
    aggregator_type: Optional[str] = None) -> Optional[RssAggregator]:
    return try_get_miniflux_aggregator(logging_in_endpoint, logging_in_username, logging_in_password, aggregator_type)
