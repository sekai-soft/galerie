from flask import Blueprint, render_template, g
from flask_babel import _
from galerie_flask.pages_blueprint import catches_exceptions, requires_auth


feed_maintenance_bp = Blueprint('feed_maintenance', __name__, template_folder='.')


@feed_maintenance_bp.route("/feed_maintenance")
@catches_exceptions
@requires_auth
def feed_maintenance_page():
    feeds = g.aggregator.get_feeds()
    dead_feeds = list(filter(lambda f: f.error, feeds))
    dead_feeds.sort(key=lambda f: f.url)

    return render_template(
        'feed_maintenance.html',
        dead_feeds=dead_feeds,
    )
