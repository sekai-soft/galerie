from flask import request, Blueprint
from flask_babel import _
from galerie_flask.actions_blueprint import make_toast
from galerie_flask.utils import requires_auth
from galerie_flask.db import db, Session


session_management_bp = Blueprint('session_management_action', __name__)


@session_management_bp.route('/rename_current_session', methods=['POST'])
@requires_auth
def rename_current_session():
    session_token = request.cookies.get('session_token')
    if not session_token:
        return make_toast(400, _("No session token found"))

    name = request.form.get('name')
    if name is None:
        return make_toast(400, _("Name is required"))

    session = db.session.query(Session).filter_by(uuid=session_token).first()
    if not session:
        return make_toast(404, _("Session not found"))

    session.name = name
    db.session.commit()

    return make_toast(200, _("Session renamed"))


@session_management_bp.route('/terminate_all_other_sessions', methods=['POST'])
@requires_auth
def terminate_all_other_sessions():
    session_token = request.cookies.get('session_token')
    if not session_token:
        return make_toast(400, _("No session token found"))

    current_session = db.session.query(Session).filter_by(uuid=session_token).first()
    if not current_session:
        return make_toast(404, _("Current session not found"))

    # Delete all sessions for this user except the current one
    deleted_count = db.session.query(Session).filter(
        Session.user_uuid == current_session.user_uuid,
        Session.uuid != session_token
    ).delete()
    db.session.commit()

    return make_toast(200, _("Terminated {} other session(s)").format(deleted_count))
