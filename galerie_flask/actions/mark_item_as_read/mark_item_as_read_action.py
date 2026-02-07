import json
from flask import g, Blueprint, make_response, request
from galerie_flask.actions_blueprint import catches_exceptions, requires_auth, make_toast


mark_item_as_read_bp = Blueprint('mark_item_as_read', __name__)


@mark_item_as_read_bp.route('/mark_item_as_read', methods=['POST'])
@catches_exceptions
@requires_auth
def mark_item_as_read():
    scroll_as_read = request.cookies.get('scroll_as_read', '0') == '1'
    if not scroll_as_read:
        return make_response()

    iid = request.args.get('iid')
    if not iid:
        return make_toast(400, "iid is required")

    g.aggregator.mark_items_as_read([iid])

    resp = make_response()
    resp.headers['HX-Trigger'] = json.dumps({
        "mark_as_read": [iid]
    })
    return resp
