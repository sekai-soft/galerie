from typing import Any
from flask import Blueprint, render_template, g
from flask_babel import _
from galerie.twitter import is_nitter_url, extract_twitter_handle_from_nitter_feed_url, check_twitter_handle_status
from galerie_flask.pages_blueprint import catches_exceptions, requires_auth


feed_maintenance_bp = Blueprint('feed_maintenance', __name__, template_folder='.')


@feed_maintenance_bp.route("/feed_maintenance")
@catches_exceptions
@requires_auth
def feed_maintenance_page():
    feeds = g.aggregator.get_feeds()
    dead_feeds = list(filter(lambda f: f.error, feeds))
    dead_feeds.sort(key=lambda f: f.url)

    dead_feeds_by_reason = {
        'x_absent': [],
        'x_suspended': [],
        'timeout': [],
        'x_protected': []
    }
    for feed in dead_feeds:
        reason = None
        if is_nitter_url(feed.url):
            handle = extract_twitter_handle_from_nitter_feed_url(feed.url)
            if handle:
                status = check_twitter_handle_status(handle)
                reason = f"x_{status}"
            else:
                reason = feed.error_reason
        elif "Client.Timeout" in feed.error_reason:
            reason = "timeout"
        else:
            reason = feed.error_reason
        
        dead_feeds_by_reason[reason] = dead_feeds_by_reason.get(reason, []) + [feed]

    return render_template(
        'feed_maintenance.html',
        dead_feeds_by_reason=dead_feeds_by_reason
    )
