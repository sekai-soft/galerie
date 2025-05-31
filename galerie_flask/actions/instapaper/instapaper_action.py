import requests
from flask import request, Blueprint, g
from flask_babel import _
from requests.auth import HTTPBasicAuth
from galerie_flask.instapaper import get_instapaper_auth, is_instapaper_available
from galerie_flask.actions_blueprint import make_toast
from galerie_flask.utils import requires_auth


instapaper_bp = Blueprint('instapaper', __name__)


@instapaper_bp.route('/instapaper', methods=['POST'])
@requires_auth
def instapaper():
    if not is_instapaper_available():
        return make_toast(400, "Instapaper was not configured")
    username_or_email, password = get_instapaper_auth()

    iid = request.args.get('iid')
    if not iid:
        return make_toast(400, "iid is required")
    
    item = g.aggregator.get_item(iid)
    if not item:
        return make_toast(400, "Item not found")
    
    instapaper_data = {
        "url": item.url,
        "title": item.title,
        "selection": item.text, # optional, plain text, no HTML, UTF-8. Will show up as the description under an item in the interface.
    }

    add_res = requests.post(
        "https://www.instapaper.com/api/add",
        auth=HTTPBasicAuth(username_or_email, password),
        data=instapaper_data
    )
    if add_res.status_code != 201:
        return make_toast(400, _('Failed to add to Instapaper',))

    return make_toast(200, _('Saved to Instapaper'))
