from flask import Blueprint
from .instapaper.instapaper_action import instapaper_bp
from .download_media.download_media_action import download_media_bp
from .load_more.load_more_action import load_more_bp
from .set_max_items.set_max_items_action import set_max_items_bp
from .set_max_rendered_items.set_max_rendered_items_action import set_max_rendered_items_bp


actions_bp = Blueprint('actions', __name__, url_prefix='/actions')
actions_bp.register_blueprint(instapaper_bp)
actions_bp.register_blueprint(download_media_bp)
actions_bp.register_blueprint(load_more_bp)
actions_bp.register_blueprint(set_max_items_bp)
actions_bp.register_blueprint(set_max_rendered_items_bp)
