from flask import request, g, Blueprint, make_response
from flask_babel import _
from galerie_flask.actions_blueprint import catches_exceptions, requires_auth, make_toast


mark_group_as_read_bp = Blueprint('mark_group_as_read', __name__)


@mark_group_as_read_bp.route('/mark_group_as_read', methods=['POST'])
@catches_exceptions
@requires_auth
def mark_group_as_read():
    group = request.args.get('group')
    if not group:
        return make_toast(400, _("Group is required"))

    g.aggregator.mark_all_group_items_as_read(group)

    resp = make_response()
    resp.headers['HX-Refresh'] = "true"
    return resp
