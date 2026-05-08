from flask import Blueprint, redirect, render_template, g, request
from flask_babel import _
from galerie_flask.pages_blueprint import catches_exceptions, no_cache, requires_auth


manage_feeds_bp = Blueprint('manage_feed', __name__, template_folder='.')


@manage_feeds_bp.route("/manage_feeds")
@catches_exceptions
@requires_auth
@no_cache
def manage_feeds_page():
    groups = g.aggregator.get_groups()
    if not groups:
        raise ValueError("No groups found")
    groups = sorted(groups, key=lambda group: group.feed_count, reverse=True)

    gid = request.args.get('group')
    if gid is None:
        return redirect(f'/manage_feeds?group={groups[0].gid}')
    
    feeds = g.aggregator.get_feeds_by_group_id(gid)
    feeds = sorted(feeds, key=lambda feed: (0 if feed.error else 1, feed.title))

    feed_counts = {}
    for group in groups:
        feed_counts[group.gid] = group.feed_count

    return render_template(
        'manage_feeds.html',
        groups=groups,
        gid=gid,
        feeds=feeds,
        feed_counts=feed_counts,
    )
