import os
from functools import wraps
from urllib.parse import urlparse
from sentry_sdk import capture_exception
from flask import Blueprint, redirect, render_template, g, request, jsonify, make_response
from flask_babel import _
from galerie.feed_filter import FeedFilter
from galerie.rendered_item import convert_rendered_items, convert_rendered_item
from galerie.twitter import extract_twitter_handle_from_feed_url, extract_twitter_handle_from_url
from .utils import requires_auth, max_items, load_more_button_args,\
    mark_as_read_button_args, items_args, add_image_ui_extras
from .get_aggregator import get_aggregator
from .instapaper import get_instapaper_auth, is_instapaper_available


def get_base_url():
    if 'BASE_URL' not in os.environ:
        return ''
    base_url = os.environ['BASE_URL']
    if base_url.endswith('/'):
        return base_url[:-1]
    return base_url


pages_blueprint = Blueprint('pages', __name__, static_folder='static', template_folder='templates')


def catches_exceptions(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            if os.getenv('DEBUG', '0') == '1':
                raise e
            capture_exception(e)
            return render_template('error.html', error=str(e))
    return decorated_function


def no_cache(view_function):
    @wraps(view_function)
    def decorated_function(*args, **kwargs):
        response = make_response(view_function(*args, **kwargs))
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response
    return decorated_function


@pages_blueprint.route("/manifest.json")
def pwa_manifest():
    return jsonify({
        "theme_color": "#1a1a1a",
        "background_color": "#1a1a1a",
        "icons": [
            {
                "purpose": "maskable",
                "sizes": "512x512",
                "src": "icon512_maskable.png",
                "type": "image/png"
            },
            {
                "purpose": "any",
                "sizes": "512x512",
                "src": "icon512_rounded.png",
                "type": "image/png"
            }
        ],
        "orientation": "any",
        "display": "standalone",
        "dir": "auto",
        "lang": "en-US",
        "name": "Galerie",
        "short_name": "Galerie",
        "start_url": get_base_url(),
        "share_target": {
            "action": "add_feed",
            "method": "GET",
            "params": {
                "title": "title",
                "text": "text",
                "url": "url"
            }
        }
    })


@pages_blueprint.route("/login")
@catches_exceptions
def login_page():
    aggregator, _ = get_aggregator()
    if aggregator:
        return redirect('/')
    next_url = request.args.get('next', '/')
    return render_template('login.html', next_url=next_url)


@pages_blueprint.route("/signup")
@catches_exceptions
def signup_page():
    next_url = request.args.get('next', '/')
    return render_template('signup.html', next_url=next_url)


@pages_blueprint.route("/")
@catches_exceptions
@requires_auth
def index_page():
    sort_by = request.args.get('sort', 'desc') == 'desc'
    gid = request.args.get('group') if request.args.get('group') else None
    infinite_scroll = request.cookies.get('infinite_scroll', '1') == '1'

    feed_filter = FeedFilter(gid)
    if sort_by:
        unread_items = g.aggregator.get_unread_items_by_iid_descending(max_items, None, feed_filter)
    else:
        unread_items = g.aggregator.get_unread_items_by_iid_ascending(max_items, None, feed_filter)

    rendered_items = convert_rendered_items(unread_items)
    for rendered_item in rendered_items:
        add_image_ui_extras(rendered_item)
    last_iid = unread_items[-1].iid if unread_items else ''

    groups = g.aggregator.get_groups()
    gids = [group.gid for group in groups]
    all_group_unread_counts = g.aggregator.get_unread_items_count_by_group_ids(gids)
    all_unread_count = sum(all_group_unread_counts.values())
    groups = sorted(groups, key=lambda group: all_group_unread_counts[group.gid], reverse=True)   
    selected_group = next((group for group in groups if group.gid == gid), None)
    remaining_count = (all_group_unread_counts[gid] if gid is not None else all_unread_count)
    remaining_count = remaining_count - max_items if remaining_count > max_items else 0
    all_feed_count = sum(group.feed_count for group in groups)

    args = {
        "groups": groups,
        "all_group_unread_counts": all_group_unread_counts,
        "all_unread_count": all_unread_count,
        "selected_group": selected_group,
        "sort_by_desc":sort_by,
        "last_iid": last_iid,
        "all_feed_count": all_feed_count
    }
    items_args(args, rendered_items, True, gid is None)
    
    load_more_button_args(args, last_iid, gid, sort_by, infinite_scroll, remaining_count)
    mark_as_read_button_args(args, gid, sort_by)

    return render_template('index.html', **args)


@pages_blueprint.route("/settings")
@catches_exceptions
@requires_auth
def settings_page():
    connection_info = g.aggregator.connection_info()
    infinite_scroll = request.cookies.get('infinite_scroll', '1') == '1'
    instapaper_available = is_instapaper_available()
    instapaper_auth = None
    if instapaper_available:
        instapaper_auth = get_instapaper_auth()
    username = g.aggregator.get_username()
    
    return render_template(
        'settings.html',
        connection_info=connection_info,
        infinite_scroll=infinite_scroll,
        is_instapaper_available=instapaper_available,
        instapaper_auth=instapaper_auth,
        username=username,
    )


@pages_blueprint.route("/manage_feeds")
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


@pages_blueprint.route("/feed")
@catches_exceptions
@requires_auth
def feed_page():
    fid = request.args.get('fid')
    items = g.aggregator.get_feed_items_by_iid_descending(fid)
    rendered_items = convert_rendered_items(items)

    args = {
        "feed": g.aggregator.get_feed(fid),
    }
    items_args(args, rendered_items, False, False)
    return render_template('feed.html', **args)


@pages_blueprint.route("/update_feed")
@catches_exceptions
@requires_auth
def update_feed_page():
    fid = request.args.get('fid')

    args = {
        "feed": g.aggregator.get_feed(fid),
        "groups": g.aggregator.get_groups(),
    }
    return render_template('update_feed.html', **args)


def is_valid_url(url: str) -> bool:
    try:
        urlparse(url)
        return True
    except ValueError:
        return False


bookmarklet = f"""javascript:(function() {{
  const url = `{get_base_url()}/add_feed?url=${{window.location.href}}&view_feed=1`;
  window.open(url, '_blank').focus();
}})();
"""

@pages_blueprint.route("/add_feed")
@catches_exceptions
@requires_auth
def add_feed_page():   
    args = request.args
    url = None
    if 'url' in args and is_valid_url(args['url']):
        url = args['url']
    elif 'text' in args and is_valid_url(args['text']):
        url = args['text']
    elif 'title' in args and is_valid_url(args['title']):
        url = args['title']

    add_feed_behavior = ''
    if args.get('view_feed', '0')== '1':
        add_feed_behavior += '?view_feed=1'
    if args.get('go_home', '0')== '1':
        add_feed_behavior += '?go_home=1'

    return render_template(
        'add_feed.html',
        url=url,
        bookmarklet=bookmarklet,
        groups=g.aggregator.get_groups(),
        add_feed_behavior=add_feed_behavior
    )


@pages_blueprint.route("/item")
@catches_exceptions
@requires_auth
def item_page():
    uid = request.args.get('uid')
    iid = uid.split('-')[0]
    u_index = int(uid.split('-')[1])

    item = g.aggregator.get_item(iid)
    rendered_items = convert_rendered_item(item, ignore_rendered_items_cap=True)
    for rendered_item in rendered_items:
        add_image_ui_extras(rendered_item)

    feed_icon = g.aggregator.get_feed_icon(item.fid)

    rt = None
    item_url = item.url
    item_url_twitter_handle = extract_twitter_handle_from_url(item_url)
    if item_url_twitter_handle:
        feed = g.aggregator.get_feed(item.fid)
        feed_url = feed.features["feed_url"]
        feed_url_twitter_handle = extract_twitter_handle_from_feed_url(feed_url)
        if feed_url_twitter_handle and feed_url_twitter_handle != item_url_twitter_handle:
            rt = item_url_twitter_handle

    return render_template(
        'item.html',
        feed_icon=feed_icon,
        rt=rt,
        item=rendered_items[0],
        items=rendered_items,
        u_index=u_index,
        is_instapaper_available=is_instapaper_available()
    )


@pages_blueprint.route("/feed_maintenance")
@catches_exceptions
@requires_auth
def feed_maintenance_page():   
    feeds = g.aggregator.get_feeds()
    dead_feeds = list(filter(lambda f: f.error, feeds))

    maybe_duplicated_twitter_feeds = {}
    for feed in feeds:
        if feed.features.get('twitter_handle'):
            twitter_handle = feed.features['twitter_handle'].lower()
            if twitter_handle not in maybe_duplicated_twitter_feeds:
                maybe_duplicated_twitter_feeds[twitter_handle] = []
            maybe_duplicated_twitter_feeds[twitter_handle].append(feed.fid)

    duplicated_twitter_feeds = []
    for twitter_handle, feed_fids in maybe_duplicated_twitter_feeds.items():
        if len(feed_fids) > 1:
            duplicated_twitter_feeds.append((twitter_handle, feed_fids))
    duplicated_twitter_feeds = sorted(duplicated_twitter_feeds, key=lambda feed: feed[0])

    return render_template(
        'feed_maintenance.html',
        dead_feeds=dead_feeds,
        duplicated_twitter_feeds=duplicated_twitter_feeds
    )


@pages_blueprint.route("/update_group")
@catches_exceptions
@requires_auth
def update_group_page():
    gid = request.args.get('group')

    return render_template(
        'update_group.html',
        group=g.aggregator.get_group(gid),
    )


@pages_blueprint.route("/manage_groups")
@catches_exceptions
@requires_auth
@no_cache
def manage_groups_page():
    groups = g.aggregator.get_groups()
    if not groups:
        raise ValueError("No groups found")
    groups = sorted(groups, key=lambda group: group.gid, reverse=True)

    return render_template(
        'manage_groups.html',
        groups=groups,
    )


@pages_blueprint.route("/add_group")
@catches_exceptions
@requires_auth
def add_group_page():
    return render_template('add_group.html')


@pages_blueprint.route("/debug")
@catches_exceptions
@requires_auth
def debug_page():
    return render_template('debug.html')
