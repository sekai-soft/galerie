from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)


class User(db.Model):
    __tablename__ = 'users'
    uuid: Mapped[str] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(unique=True)
    user_password_hashed: Mapped[str]
    miniflux_password: Mapped[str]
    feed_limit: Mapped[int]
    history_limit: Mapped[int]
    created_at: Mapped[str] = mapped_column(db.DateTime, server_default=db.func.now())


class Session(db.Model):
    __tablename__ = 'sessions'
    uuid: Mapped[str] = mapped_column(primary_key=True)
    user_uuid: Mapped[str] = mapped_column(db.ForeignKey('users.uuid'))
    csrf_token: Mapped[str]
    name: Mapped[str]
    created_at: Mapped[str] = mapped_column(db.DateTime, server_default=db.func.now())
    accessed_at: Mapped[str] = mapped_column(db.DateTime)


class InstapaperConnection(db.Model):
    __tablename__ = 'instapaper_connections'
    uuid: Mapped[str] = mapped_column(primary_key=True)
    user_uuid: Mapped[str] = mapped_column(db.ForeignKey('users.uuid'))
    instapaper_username: Mapped[str]
    instapaper_password: Mapped[str]
    created_at: Mapped[str] = mapped_column(db.DateTime, server_default=db.func.now())


class ItemViewHistory(db.Model):
    __tablename__ = 'item_view_history'
    uuid: Mapped[str] = mapped_column(primary_key=True)
    user_uuid: Mapped[str] = mapped_column(db.ForeignKey('users.uuid'))
    item_uid: Mapped[str]
    miniflux_entry: Mapped[dict] = mapped_column(db.JSON)
    created_at: Mapped[str] = mapped_column(db.DateTime, server_default=db.func.now())
