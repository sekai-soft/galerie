import os
from typing import Optional, Tuple
from flask import request
from galerie.rss_aggregator import RssAggregator
from galerie.miniflux_aggregator import MinifluxAggregator
from .miniflux_admin import get_miniflux_admin


def get_aggregator(login_username: Optional[str]=None, login_password: Optional[str]=None) -> Optional[Tuple[RssAggregator, Optional[str]]]:
    # self-hosted instance
    env_endpoint = os.getenv('MINIFLUX_ENDPOINT')
    env_username = os.getenv('MINIFLUX_USERNAME')
    env_password = os.getenv('MINIFLUX_PASSWORD')
    if env_endpoint and env_username and env_password:
        return MinifluxAggregator(
            env_endpoint,
            env_username,
            env_password,
            False
        ), None
    
    # managed instance
    miniflux_admin = get_miniflux_admin()
    
    session_token = request.cookies.get('session_token')
    if not session_token:
        if not login_username or not login_password:
            return None, None
        session_token = miniflux_admin.log_in(login_username, login_password)
    
    miniflux_username, miniflux_password = miniflux_admin.verify_session(session_token)
    return MinifluxAggregator(
        miniflux_admin.base_url,
        miniflux_username,
        miniflux_password,
        True
    ), session_token
