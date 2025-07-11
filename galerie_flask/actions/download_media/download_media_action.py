import os
import io
import requests
import tempfile
import zipfile
from flask import request, Blueprint, g, send_file, after_this_request
from galerie.rendered_item import convert_rendered_item
from galerie_flask.actions_blueprint import make_toast
from galerie_flask.utils import requires_auth, DEFAULT_MAX_RENDERED_ITEMS


download_media_bp = Blueprint('download_media', __name__)


def _download_media(urls: list[str], iid: str):
    if len(urls) == 1:
        url = urls[0]
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        content_type = response.headers.get('Content-Type', 'application/octet-stream')

        file_data = io.BytesIO(response.content)
        file_data.seek(0)

        filename = url.split('/')[-1].split('?')[0]

        return send_file(
            file_data,
            mimetype=content_type,
            as_attachment=True,
            download_name=filename
        )

    temp_zip = tempfile.NamedTemporaryFile(delete=True, suffix='.zip')
    try:
        with zipfile.ZipFile(temp_zip.name, 'w') as zipf:
            for url in urls:
                response = requests.get(url, timeout=10)
                response.raise_for_status()

                filename = url.split('/')[-1].split('?')[0]
                    
                zipf.writestr(filename, response.content)
        
        # Send the zip file
        return send_file(
            temp_zip.name,
            mimetype='application/zip',
            as_attachment=True,
            download_name=f"media_{iid}.zip"
        )
    finally:
        # Clean up temp file (after response is sent)
        @after_this_request
        def _remove_file(response):
            if os.path.exists(temp_zip.name):
                os.unlink(temp_zip.name)
            return response


@download_media_bp.route('/download_media')
@requires_auth
def download_media():
    uid = request.args.get('uid')
    if not uid:
        return make_toast(400, "uid is required")
    
    iid = int(uid.split('-')[0])
    u_index = int(uid.split('-')[1])
    
    item = g.aggregator.get_item(iid)
    if not item:
        return make_toast(400, "Item not found")

    rendered_items = convert_rendered_item(item, DEFAULT_MAX_RENDERED_ITEMS, ignore_rendered_items_cap=True)
    ri = rendered_items[u_index] if u_index < len(rendered_items) else None
    if not ri:
        return make_toast(400, "Rendered item not found")
    
    url = None
    if ri.video_url:
        url = ri.video_url
    elif ri.image_url:
        url = ri.image_url
    if not url:
        return make_toast(400, "No media URL found in the item")

    return _download_media([url], iid)


@download_media_bp.route('/download_all_media')
@requires_auth
def download_all_media():
    iid = request.args.get('iid')
    if not iid:
        return make_toast(400, "iid is required")

    item = g.aggregator.get_item(iid)
    if not item:
        return make_toast(400, "Item not found")

    rendered_items = convert_rendered_item(item, DEFAULT_MAX_RENDERED_ITEMS, ignore_rendered_items_cap=True)
    urls = []
    for ri in rendered_items:
        if ri.video_url:
            urls.append(ri.video_url)
        elif ri.image_url:
            urls.append(ri.image_url)

    return _download_media(urls, iid)
