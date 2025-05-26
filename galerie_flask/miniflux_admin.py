import os
import enum
import datetime
import secrets
import miniflux
from typing import Tuple
from uuid import uuid4
from werkzeug.security import generate_password_hash, check_password_hash
from galerie.miniflux_aggregator import MinifluxAggregator
from galerie.group import PREVIEW_GROUP_TITLE
from .db import db, User, Session


STARTING_FEED_LIMIT = 50
SESSION_EXPIRY_DAYS = 14


class MinifluxAdminErrorCode(enum.Enum):
    USERNAME_ALREADY_EXISTS = 0
    WRONG_CREDENTIALS = 1
    LOGGED_OUT = 2
    ABSENT_USER = 3
    SESSION_EXPIRED = 4


class MinifluxAdminException(Exception):
    def __init__(self, error_code: MinifluxAdminErrorCode):
        self.error_code = error_code


class MinifluxAdmin(object):
    def __init__(self, base_url: str, admin_username: str, admin_password: str):
        self.base_url = base_url
        self.client = miniflux.Client(base_url, admin_username, admin_password)


    def sign_up(self, username: str, user_password: str):
        user_with_same_username = db.session.query(User).filter_by(username=username).first()
        if user_with_same_username:
            raise MinifluxAdminException(MinifluxAdminErrorCode.USERNAME_ALREADY_EXISTS)

        miniflux_password = secrets.token_urlsafe(16)
        new_user = User(
            uuid=str(uuid4()),
            username=username,
            user_password_hashed=generate_password_hash(user_password),
            miniflux_password=miniflux_password,
            feed_limit=STARTING_FEED_LIMIT
        )
        db.session.add(new_user)
        db.session.commit()

        self.client.create_user(username, miniflux_password)

        miniflux_aggregator = MinifluxAggregator(
            self.base_url,
            username,
            miniflux_password,
            True
        )
        miniflux_aggregator.create_preview_group()


    def log_in(self, username: str, password: str) -> str:
        user = db.session.query(User).filter_by(username=username).first()
        if not user:
            raise MinifluxAdminException(MinifluxAdminErrorCode.WRONG_CREDENTIALS)
        if not check_password_hash(user.user_password_hashed, password):
            raise MinifluxAdminException(MinifluxAdminErrorCode.WRONG_CREDENTIALS)

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
            raise MinifluxAdminException(MinifluxAdminErrorCode.LOGGED_OUT)
        
        if session.created_at < datetime.datetime.now() - datetime.timedelta(days=SESSION_EXPIRY_DAYS):
            db.session.delete(session)
            db.session.commit()
            raise MinifluxAdminException(MinifluxAdminErrorCode.SESSION_EXPIRED)

        user = db.session.query(User).filter_by(uuid=session.user_uuid).first()
        if not user:
            raise MinifluxAdminException(MinifluxAdminErrorCode.ABSENT_USER)
        
        session.accessed_at = datetime.datetime.now()
        db.session.commit()

        return user.username, user.miniflux_password
    

    def log_out(self, session_uuid: str):
        session = db.session.query(Session).filter_by(uuid=session_uuid).first()
        if not session:
            raise MinifluxAdminException(MinifluxAdminErrorCode.LOGGED_OUT)

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
