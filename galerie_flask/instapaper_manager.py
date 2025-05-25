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

        return instapaper_connection.username, instapaper_connection.password


def get_instapaper_manager() -> InstapaperManager:
    return InstapaperManager()
