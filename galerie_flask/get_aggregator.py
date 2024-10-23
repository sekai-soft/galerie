import os
import base64
import json
from typing import Optional
from flask import request
from galerie.rss_aggregator import RssAggregator
from galerie.fever_aggregator import FeverAggregator
from galerie.miniflux_aggregator import MinifluxAggregator
from galerie.inoreader_aggregator import InoreaderAggregator


def check_inoreader_env():
    # determine if required environment variables are present
    env_app_id = os.getenv('INOREADER_APP_ID')
    env_app_key = os.getenv('INOREADER_APP_KEY')
    env_base_url = os.getenv('BASE_URL')
    return env_app_id and env_app_key and env_base_url


def try_get_inoreader_aggregator(
        access_token: Optional[str] = None,
        refresh_token: Optional[str] = None,
        expires_at: Optional[float] = None) -> Optional[InoreaderAggregator]:
    if not check_inoreader_env():
        return None
    app_id = os.getenv('INOREADER_APP_ID')
    app_key = os.getenv('INOREADER_APP_KEY')

    # determine from oauth callback
    if access_token and refresh_token and expires_at:
        return InoreaderAggregator(
            app_id=app_id,
            app_key=app_key,
            access_token=access_token,
            refresh_token=refresh_token,
            expires_at=expires_at)

    # determine from persisted auth
    auth_cookie = request.cookies.get('auth')
    if auth_cookie:
        auth = base64.b64decode(auth_cookie).decode('utf-8')
        auth = json.loads(auth)
        is_inoreader = auth.get('inoreader', False)
        if is_inoreader:
            cookie_access_token = auth.get('access_token')
            cookie_refresh_token = auth.get('refresh_token')
            cookie_expires_at = auth.get('expires_at')
            return InoreaderAggregator(app_id=app_id,
                app_key=app_key,
                access_token=cookie_access_token,
                refresh_token=cookie_refresh_token,
                expires_at=cookie_expires_at)

    return None

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


def try_get_fever_aggregator(
        logging_in_endpoint: Optional[str] = None,
        logging_in_username: Optional[str] = None,
        logging_in_password: Optional[str] = None) -> Optional[FeverAggregator]:
    # determine in env
    env_endpoint = os.getenv('FEVER_ENDPOINT')
    env_username = os.getenv('FEVER_USERNAME')
    env_password = os.getenv('FEVER_PASSWORD')
    if env_endpoint and env_username and env_password:
        return FeverAggregator(env_endpoint, env_username, env_password, False)

    # determine from login form
    if logging_in_endpoint and logging_in_username is not None and logging_in_password is not None:
        return FeverAggregator(logging_in_endpoint, logging_in_username, logging_in_password, True)

    # determine from persisted auth
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
    logging_in_password: Optional[str] = None,
    aggregator_type: Optional[str] = None) -> Optional[RssAggregator]:
    aggregator = try_get_inoreader_aggregator()
    if aggregator:
        return aggregator
    aggregator = try_get_miniflux_aggregator(logging_in_endpoint, logging_in_username, logging_in_password, aggregator_type)
    if aggregator:
        return aggregator
    return try_get_fever_aggregator(logging_in_endpoint, logging_in_username, logging_in_password)
