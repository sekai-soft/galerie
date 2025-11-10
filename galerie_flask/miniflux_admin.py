import os
import datetime
import secrets
import miniflux
from typing import Tuple
from uuid import uuid4
from flask_babel import _
from werkzeug.security import generate_password_hash, check_password_hash
from .db import db, User, Session


STARTING_FEED_LIMIT = 50
STARTING_HISTORY_LIMIT = 500
SESSION_EXPIRY_DAYS = 14
admin_username = os.getenv('ADMIN_USERNAME')


class MinifluxAdminException(Exception):
    def __init__(self, status_code: int, human_readable_message: str, expected: bool):
        self.status_code = status_code
        self.human_readable_message = human_readable_message
        self.expected = expected


class MinifluxAdmin(object):
    def __init__(self, base_url: str, admin_username: str, admin_password: str):
        self.base_url = base_url
        self.client = miniflux.Client(base_url, admin_username, admin_password)


    def sign_up(self, username: str, user_password: str):
        if username == admin_username:
            raise MinifluxAdminException(400, _("Username already exists"), True)

        user_with_same_username = db.session.query(User).filter_by(username=username).first()
        if user_with_same_username:
            raise MinifluxAdminException(400, _("Username already exists"), True)

        miniflux_password = secrets.token_urlsafe(16)
        new_user = User(
            uuid=str(uuid4()),
            username=username,
            user_password_hashed=generate_password_hash(user_password),
            miniflux_password=miniflux_password,
            feed_limit=STARTING_FEED_LIMIT,
            history_limit=STARTING_HISTORY_LIMIT
        )
        db.session.add(new_user)
        db.session.commit()

        self.client.create_user(username, miniflux_password)


    def log_in(self, username: str, password: str) -> str:
        if username == admin_username:
            raise MinifluxAdminException(400, _("Username already exists"), True)

        user = db.session.query(User).filter_by(username=username).first()
        if not user:
            raise MinifluxAdminException(400, _("Wrong credentials"), True)
        if not check_password_hash(user.user_password_hashed, password):
            raise MinifluxAdminException(400, _("Wrong credentials"), True)

        session_uuid = str(uuid4())
        new_session = Session(
            uuid=session_uuid,
            user_uuid=user.uuid,
            csrf_token=secrets.token_urlsafe(32),
            name="",
            accessed_at=datetime.datetime.now()
        )
        db.session.add(new_session)
        db.session.commit()

        return session_uuid


    def verify_session(self, session_uuid: str) -> Tuple[str, str]:
        session = db.session.query(Session).filter_by(uuid=session_uuid).first()
        if not session:
            raise MinifluxAdminException(401, "Logged out", False)
        
        if session.created_at < datetime.datetime.now() - datetime.timedelta(days=SESSION_EXPIRY_DAYS):
            db.session.delete(session)
            db.session.commit()
            raise MinifluxAdminException(401, _("Your session has expired. Please log in again."), True)

        user = db.session.query(User).filter_by(uuid=session.user_uuid).first()
        if not user:
            raise MinifluxAdminException(404, "User not found", False)
        
        session.accessed_at = datetime.datetime.now()
        db.session.commit()

        return user.username, user.miniflux_password
    

    def log_out(self, session_uuid: str):
        session = db.session.query(Session).filter_by(uuid=session_uuid).first()
        if not session:
            return

        db.session.delete(session)
        db.session.commit()


def get_miniflux_admin() -> MinifluxAdmin:
    miniflux_base_url = os.getenv('MINIFLUX_BASE_URL')
    miniflux_admin_username = os.getenv('ADMIN_USERNAME')
    miniflux_admin_password = os.getenv('ADMIN_PASSWORD')
    if not miniflux_base_url or not miniflux_admin_username or not miniflux_admin_password:
        raise ValueError(
            'MINIFLUX_BASE_URL, ADMIN_USERNAME, and ADMIN_PASSWORD must be set in the environment variables.'
        )
    return MinifluxAdmin(
        miniflux_base_url,
        miniflux_admin_username,
        miniflux_admin_password
    )
