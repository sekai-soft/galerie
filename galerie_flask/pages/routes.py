from flask import Blueprint
from .item.item_page import item_bp
from .feed_maintenance.feed_maintenamce_page import feed_maintenance_bp
from .settings.settings_page import settings_bp


pages_bp = Blueprint('pages', __name__, url_prefix='/')
pages_bp.register_blueprint(item_bp)
pages_bp.register_blueprint(feed_maintenance_bp)
pages_bp.register_blueprint(settings_bp)
