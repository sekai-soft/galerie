import os
from typing import Tuple, Optional
from flask import request
from .instapaper_manager import get_instapaper_manager


def get_instapaper_auth() -> Optional[Tuple[str, str]]:
    # self-hosted
    env_username = os.environ.get('INSTAPAPER_USERNAME')
    env_password = os.environ.get('INSTAPAPER_PASSWORD')
    if env_username and env_password:
        return env_username, env_password
    
    # managed
    session_token = request.cookies.get('session_token')
    if not session_token:
        return None, None

    instapaper_manager = get_instapaper_manager()
    return instapaper_manager.get_instapaper_credentials(session_token)


def is_instapaper_available() -> bool:
    session_token = request.cookies.get('session_token')
    if not session_token:
        # self-hosted
        env_username = os.environ.get('INSTAPAPER_USERNAME')
        env_password = os.environ.get('INSTAPAPER_PASSWORD')
        return env_username and env_password
    
    # managed
    instapaper_manager = get_instapaper_manager()
    return instapaper_manager.get_instapaper_credentials(session_token) is not None
