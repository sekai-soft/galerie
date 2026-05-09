from flask import Blueprint, redirect, render_template, g, request
from flask_babel import _
from galerie_flask.pages_blueprint import catches_exceptions, no_cache, requires_auth


manage_feeds_bp = Blueprint('manage_feed', __name__, template_folder='.')


@manage_feeds_bp.route("/manage_feeds")
@catches_exceptions
@requires_auth
@no_cache
def manage_feeds_page():
    gid: str = request.args.get('group', '_all')
    sort = request.args.get('sort', 'order_desc')

    groups = g.aggregator.get_groups()
    groups = sorted(groups, key=lambda group: group.feed_count, reverse=True)
    all_feeds = g.aggregator.get_feeds()
    
    if gid == '_all':
        feeds = all_feeds
    else:
        feeds = g.aggregator.get_feeds_by_group_id(gid)
    def feed_sort_key(feed):
        if sort == 'order_desc':
            return 0 if feed.error else 1, -feed.order_added
        elif sort == 'order_asc':
            return 0 if feed.error else 1, feed.order_added
        # sort == 'ab'
        return 0 if feed.error else 1, feed.title
    feeds = sorted(feeds, key=feed_sort_key)

    return render_template(
        'manage_feeds.html',
        sort=sort,
        groups=groups,
        gid=gid,
        feeds=feeds,
        all_feed_count=len(all_feeds)
    )
