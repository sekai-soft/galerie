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

    # Pack each feed with its Twitter status in a tuple (feed, status_string)
    # status_string is one of: "absent", "suspended", "protected", or None
    dead_feeds_with_status = []
    for feed in dead_feeds:
        status = None
        if is_nitter_url(feed.url):
            handle = extract_twitter_handle_from_nitter_feed_url(feed.url)
            if handle:
                status = check_twitter_handle_status(handle)
        dead_feeds_with_status.append((feed, status))

    # Sort by status priority (absent, suspended, None, protected) then by feed URL alphabetically
    status_priority = {'absent': 0, 'suspended': 1, None: 2, 'protected': 3}
    dead_feeds_with_status.sort(key=lambda x: (status_priority.get(x[1], 2), x[0].url))

    return render_template(
        'feed_maintenance.html',
        dead_feeds=dead_feeds_with_status,
    )
