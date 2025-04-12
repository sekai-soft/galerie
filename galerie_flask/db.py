from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)


class User(db.Model):
    username: Mapped[str] = mapped_column(primary_key=True)
    passkey_user_id: Mapped[str] = mapped_column()


class Passkey(db.Model):
    passkey_id: Mapped[str] = mapped_column(primary_key=True)
    passkey_user_id: Mapped[str] = mapped_column()
    public_key: Mapped[str] = mapped_column()
    backed_up: Mapped[bool] = mapped_column()
    name: Mapped[str] = mapped_column()
    transports: Mapped[str] = mapped_column()


class PasskeyChallengeSession(db.Model):
    session_id: Mapped[str] = mapped_column(primary_key=True)
    challenge: Mapped[str] = mapped_column()
    passkey_user_id: Mapped[str] = mapped_column()
