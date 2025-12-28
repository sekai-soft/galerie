from flask import g, Blueprint, make_response
from flask_babel import _
from galerie_flask.actions_blueprint import catches_exceptions, requires_auth, make_toast


mark_all_as_read_bp = Blueprint('mark_all_as_read', __name__)


@mark_all_as_read_bp.route('/mark_all_as_read', methods=['POST'])
@catches_exceptions
@requires_auth
def mark_all_as_read():
    g.aggregator.mark_all_items_as_read()

    resp = make_response()
    resp.headers['HX-Refresh'] = "true"
    return resp
