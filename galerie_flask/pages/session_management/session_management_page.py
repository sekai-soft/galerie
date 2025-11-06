from flask import Blueprint, render_template, request
from flask_babel import _
from galerie_flask.pages_blueprint import catches_exceptions, requires_auth
from galerie_flask.db import db, Session


session_management_bp = Blueprint('session_management', __name__, template_folder='.')


@session_management_bp.route("/sessions")
@catches_exceptions
@requires_auth
def session_management_page():
    # Get current session token
    session_token = request.cookies.get('session_token')

    if not session_token:
        raise ValueError("No session token found")

    # Get current session
    current_session = db.session.query(Session).filter_by(uuid=session_token).first()

    if not current_session:
        raise ValueError("Current session not found")

    # Get all other sessions for the current user (excluding current), ordered by accessed_at (most recent first)
    other_sessions = db.session.query(Session).filter(
        Session.user_uuid == current_session.user_uuid,
        Session.uuid != session_token
    ).order_by(Session.accessed_at.desc()).all()

    return render_template(
        'session_management.html',
        current_session=current_session,
        other_sessions=other_sessions,
    )
