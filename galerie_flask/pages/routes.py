from flask import Blueprint
from .item.item_page import item_bp
from .feed_maintenance.feed_maintenamce_page import feed_maintenance_bp
from .settings.settings_page import settings_bp
from .feed.feed_page import feed_bp
from .index.index_page import index_bp
from .media_proxy.media_proxy import media_proxy_bp
from .session_management.session_management_page import session_management_bp
from .item_history.item_history_page import item_history_bp


pages_bp = Blueprint('pages', __name__, url_prefix='/')
pages_bp.register_blueprint(item_bp)
pages_bp.register_blueprint(feed_maintenance_bp)
pages_bp.register_blueprint(settings_bp)
pages_bp.register_blueprint(feed_bp)
pages_bp.register_blueprint(index_bp)
pages_bp.register_blueprint(media_proxy_bp)
pages_bp.register_blueprint(session_management_bp)
pages_bp.register_blueprint(item_history_bp)
