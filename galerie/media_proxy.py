import base64
import hashlib
import hmac
import os
import time

if "GALERIE_MEDIA_PROXY_BASE_URL" not in os.environ:
    raise ValueError("GALERIE_MEDIA_PROXY_BASE_URL environment variable is not set.")
base_url = os.environ["GALERIE_MEDIA_PROXY_BASE_URL"]

if "GALERIE_MEDIA_PROXY_HMAC_KEY" not in os.environ:
    raise ValueError("GALERIE_MEDIA_PROXY_HMAC_KEY environment variable is not set.")
hmac_key_b64 = os.environ["GALERIE_MEDIA_PROXY_HMAC_KEY"]
hmac_key = base64.b64decode(hmac_key_b64)
if len(hmac_key) != 32:
    raise ValueError("GALERIE_MEDIA_PROXY_HMAC_KEY must decode to 32 bytes")

if "GALERIE_MEDIA_PROXY_URL_TTL" not in os.environ:
    raise ValueError("GALERIE_MEDIA_PROXY_URL_TTL environment variable is not set.")
url_ttl = int(os.environ["GALERIE_MEDIA_PROXY_URL_TTL"])


def sign_media_url(upstream_url: str) -> str:
    exp = str(int(time.time()) + url_ttl)
    msg = f"{exp}:{upstream_url}".encode()
    sig = hmac.new(hmac_key, msg, hashlib.sha256).digest()
    url_b64 = base64.urlsafe_b64encode(upstream_url.encode()).decode().rstrip("=")
    sig_b64 = base64.urlsafe_b64encode(sig).decode().rstrip("=")
    return f"{base_url}?url={url_b64}&exp={exp}&sig={sig_b64}"
