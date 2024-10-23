import os
from requests_oauthlib import OAuth2Session
from .rss_aggregator import AuthError

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"


def make_oauth2_session(app_id: str, base_url: str, state: str) -> OAuth2Session:
    return OAuth2Session(
        app_id,
        redirect_uri=f"{base_url}/oauth/redirect",
        scope="read write",
        state=state,
   )


def get_authorization_url(app_id: str, base_url: str, state: str) -> str:
    oauth = make_oauth2_session(app_id, base_url, state)
    authorization_url, ret_state = oauth.authorization_url("https://www.inoreader.com/oauth2/auth")
    if state != ret_state:
        raise AuthError()
    return authorization_url


def fetch_token(app_id: str, app_key: str, base_url: str, state: str, request_url: str) -> dict:
    oauth = make_oauth2_session(app_id, base_url, state)
    return oauth.fetch_token(
        "https://www.inoreader.com/oauth2/token",
        authorization_response=request_url,
        client_secret=app_key)
