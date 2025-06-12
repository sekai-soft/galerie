import requests
from flask import request, Blueprint, Response, stream_with_context
from galerie.twitter import TWITTER_VIDEO_CDN_URL
from galerie.instagram import INSTAGRAM_CDN_URL
from galerie.rednote import REDNOTE_CDN_URL_HTTP
from galerie_flask.pages_blueprint import catches_exceptions


media_proxy_bp = Blueprint('m', __name__, url_prefix='/m')


def _proxy(original_url: str):
    req = requests.get(original_url, headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    },stream=True)

    return Response(
        stream_with_context(req.iter_content(chunk_size=1024)),
        content_type=req.headers.get('content-type'),
        status=req.status_code
    )


@media_proxy_bp.route("/tv/<path:p>")
@catches_exceptions
def proxy_twitter_video(p):
    return _proxy(TWITTER_VIDEO_CDN_URL + "/" + p)


@media_proxy_bp.route("/xhs/<path:p>")
@catches_exceptions
def proxy_rednote(p):
    return _proxy(REDNOTE_CDN_URL_HTTP + p)


@media_proxy_bp.route("/ins/<path:p>")
@catches_exceptions
def proxy_instagram(p):
    url = INSTAGRAM_CDN_URL + "/" + p
    qs = request.query_string.decode('utf-8')
    if qs:
        url += '?' + qs
    return _proxy(url)
