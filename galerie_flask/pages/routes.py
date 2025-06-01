from flask import Blueprint
from .item.item_page import item_bp
from .feed_maintenance.feed_maintenamce_page import feed_maintenance_bp
from .media_proxy.media_proxy import media_proxy_bp


pages_bp = Blueprint('pages', __name__, url_prefix='/')
pages_bp.register_blueprint(item_bp)
pages_bp.register_blueprint(feed_maintenance_bp)
pages_bp.register_blueprint(media_proxy_bp)
