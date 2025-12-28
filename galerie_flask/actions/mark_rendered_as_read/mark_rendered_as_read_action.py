from flask import request, g, Blueprint, make_response
from flask_babel import _
from galerie_flask.actions_blueprint import catches_exceptions, requires_auth, make_toast


mark_rendered_as_read_bp = Blueprint('mark_rendered_as_read', __name__)


@mark_rendered_as_read_bp.route('/mark_rendered_as_read', methods=['POST'])
@catches_exceptions
@requires_auth
def mark_rendered_as_read():
    entry_ids = request.form.getlist('entry_id')
    if not entry_ids:
        return make_toast(200, _("No unread items on this page"))

    g.aggregator.mark_entries_as_read(entry_ids)

    resp = make_response()
    resp.headers['HX-Refresh'] = "true"
    return resp
