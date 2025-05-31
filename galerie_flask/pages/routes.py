from flask import Blueprint
from .item.item_route import item_bp


pages_bp = Blueprint('pages', __name__, url_prefix='/')
pages_bp.register_blueprint(item_bp)
