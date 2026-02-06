import requests
from flask import Blueprint, Response, g, stream_with_context
from galerie.rendered_item import convert_rendered_item
from galerie_flask.utils import requires_auth, DEFAULT_MAX_RENDERED_ITEMS


media_proxy_bp = Blueprint('media_proxy', __name__)


@media_proxy_bp.route('/m/<iid>/<int:media_index>')
@requires_auth
def proxy_media(iid: str, media_index: int):
    print(iid, media_index)
    item = g.aggregator.get_item(iid)
    if not item:
        return Response("item not found", status=404)

    rendered_items = convert_rendered_item(item, DEFAULT_MAX_RENDERED_ITEMS, ignore_rendered_items_cap=True, add_proxy_twitter_video_url=False)
    if media_index >= len(rendered_items):
        return Response("media index out of range", status=404)

    ri = rendered_items[media_index]

    url = ri.video_url or ri.image_url
    if not url:
        return Response("no media url found", status=404)

    try:
        # Stream the content from the source
        upstream_response = requests.get(url, stream=True, timeout=30)
        upstream_response.raise_for_status()
    except requests.RequestException as e:
        return Response(f"failed to fetch media: {str(e)}", status=502)

    # Get content type from upstream, default to video/mp4 for videos
    content_type = upstream_response.headers.get('Content-Type', 'application/octet-stream')
    content_length = upstream_response.headers.get('Content-Length')

    def generate():
        for chunk in upstream_response.iter_content(chunk_size=8192):
            yield chunk

    headers = {
        'Content-Type': content_type,
        'Accept-Ranges': 'bytes',
        'Cache-Control': 'public, max-age=86400',  # Cache for 1 day
    }

    if content_length:
        headers['Content-Length'] = content_length

    return Response(
        stream_with_context(generate()),
        status=upstream_response.status_code,
        headers=headers
    )
