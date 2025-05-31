from flask import Blueprint
from .instapaper.instapaper_action import instapaper_bp


actions_bp = Blueprint('actions', __name__, url_prefix='/actions')
actions_bp.register_blueprint(instapaper_bp)
