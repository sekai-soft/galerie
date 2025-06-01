import requests
from flask import Blueprint, Response, stream_with_context
from galerie.rednote import REDNOTE_CDN_URL_HTTP
from galerie_flask.pages_blueprint import catches_exceptions


media_proxy_bp = Blueprint('m', __name__, url_prefix='/m')


@media_proxy_bp.route("/rednote/<path:p>")
@catches_exceptions
def media_proxy(p):
    original_url = REDNOTE_CDN_URL_HTTP + p
    print(original_url)

    req = requests.get(original_url, stream=True)
    
    return Response(
        stream_with_context(req.iter_content(chunk_size=1024)),
        content_type=req.headers.get('content-type'),
        status=req.status_code
    )
