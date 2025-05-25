import uuid
from typing import Tuple, Optional
from .db import db, Session, InstapaperConnection

class InstapaperManager:
    def __init__(self):
        pass

    def get_instapaper_credentials(self, session_token: str) -> Optional[Tuple[str, str]]:
        user_id = db.session.query(Session).filter_by(uuid=session_token).first()
        if not user_id:
            return None
        
        instapaper_connection = db.session.query(InstapaperConnection).filter_by(user_uuid=user_id.user_uuid).first()
        if not instapaper_connection:
            return None

        return instapaper_connection.instapaper_username, instapaper_connection.instapaper_password

    def add_instapaper_connection(self, session_token: str, instapaper_username: str, instapaper_password: str):
        user_id = db.session.query(Session).filter_by(uuid=session_token).first()
        if not user_id:
            return

        instapaper_connection = db.session.query(InstapaperConnection).filter_by(user_uuid=user_id.user_uuid).first()
        if instapaper_connection:
            raise ValueError("Instapaper connection already exist for this user.")
        
        new_connection = InstapaperConnection(
            uuid=str(uuid.uuid4()),
            user_uuid=user_id.user_uuid,
            instapaper_username=instapaper_username,
            instapaper_password=instapaper_password
        )
        db.session.add(new_connection)
        db.session.commit()
    
    def remove_instapaper_connection(self, session_token: str):
        user_id = db.session.query(Session).filter_by(uuid=session_token).first()
        if not user_id:
            return
        
        instapaper_connection = db.session.query(InstapaperConnection).filter_by(user_uuid=user_id.user_uuid).first()
        if not instapaper_connection:
            return

        db.session.delete(instapaper_connection)
        db.session.commit()


def get_instapaper_manager() -> InstapaperManager:
    return InstapaperManager()
