import os
import json
import base64
from typing import Optional
from functools import wraps
from urllib.parse import urlparse
from sentry_sdk import capture_exception
from flask import Blueprint, redirect, render_template, g, request, make_response, jsonify
from flask_babel import _
from pocket import Pocket
from galerie.feed_filter import FeedFilter
from galerie.rendered_item import convert_rendered_items, convert_rendered_item
from galerie.twitter import extract_twitter_handle_from_feed_url, extract_twitter_handle_from_url
from .utils import requires_auth, max_items, load_more_button_args,\
    mark_as_read_button_args, items_args, add_image_ui_extras, encode_setup_from_cookies, cookie_max_age, \
    is_instapaper_available, is_pocket_available
from .get_aggregator import get_aggregator


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
        "start_url": "https://galerie-reader.app",
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
    aggregator = get_aggregator()
    if aggregator:
        return redirect('/')
    next_url = request.args.get('next', '/')
    return render_template('login.html', next_url=next_url)


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
    remaining_count = (all_group_unread_counts[gid] if gid is not None else all_unread_count) - max_items

    args = {
        "groups": groups,
        "all_group_unread_counts": all_group_unread_counts,
        "all_unread_count": all_unread_count,
        "selected_group": selected_group,
        "sort_by_desc":sort_by,
        "last_iid": last_iid,
    }
    items_args(args, rendered_items, gid is None)
    
    load_more_button_args(args, last_iid, gid, sort_by, infinite_scroll, remaining_count)
    mark_as_read_button_args(args, gid, sort_by)

    return render_template('index.html', **args)


@pages_blueprint.route("/settings")
@catches_exceptions
@requires_auth
def settings_page():
    infinite_scroll = request.cookies.get('infinite_scroll', '1') == '1'
    pocket_auth = json.loads(request.cookies.get('pocket_auth', '{}'))
    instapaper_auth = json.loads(request.cookies.get('instapaper_auth', '{}'))
    
    setup_code = encode_setup_from_cookies()
    setup_code = base64.b64encode(setup_code.encode("utf-8"))
    setup_code = setup_code.decode("utf-8")

    return render_template(
        'settings.html',
        connection_info=g.aggregator.connection_info(),
        pocket_auth=pocket_auth,
        infinite_scroll=infinite_scroll,
        setup_code=setup_code,
        instapaper_auth=instapaper_auth)


@pages_blueprint.route("/pocket_oauth")
@catches_exceptions
def pocket_oauth_redirect_page():
    consumer_key = os.environ['POCKET_CONSUMER_KEY']
    request_token = request.cookies.get('pocket_request_token')
    user_credentials = Pocket.get_credentials(consumer_key=consumer_key, code=request_token)

    resp = make_response(render_template(
        'pocket_oauth.html',
        username=user_credentials['username']))
    resp.delete_cookie('pocket_request_token')
    resp.set_cookie('pocket_auth', json.dumps(user_credentials), max_age=cookie_max_age)
    return resp


@pages_blueprint.route("/feeds")
@catches_exceptions
@requires_auth
def feeds_page():
    feeds = g.aggregator.get_feeds()
    groups = g.aggregator.get_groups()

    feeds_by_groups = []
    for group in groups:
        feeds_by_groups.append({
            "group": group,
            "feeds": [feed for feed in feeds if feed.gid == group.gid]
        })

    return render_template('feeds.html', feeds_by_groups=feeds_by_groups)


@pages_blueprint.route("/feed")
@catches_exceptions
@requires_auth
def feed_page():
    fid = request.args.get('fid')
    items = g.aggregator.get_feed_items_by_iid_descending(fid)
    rendered_items = convert_rendered_items(items)

    args = {
        "feed": g.aggregator.get_feed(fid),
        "groups": g.aggregator.get_groups(),
    }
    items_args(args, rendered_items, False)
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


bookmarklet = """javascript:(function() {
  const url = `https://galerie-reader.app/add_feed?url=${window.location.href}`;
  window.open(url, '_blank').focus();
})();
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
    
    if not url:
        return render_template('add_feed.html', groups=g.aggregator.get_groups(), bookmarklet=bookmarklet)
    twitter_handle = extract_twitter_handle_from_url(url)

    for feed in g.aggregator.get_feeds():
        feed_url = feed.features["feed_url"]
        if twitter_handle and twitter_handle == extract_twitter_handle_from_feed_url(feed_url):
            return render_template('add_feed.html', error=_("Twitter feed already exists") + " @" + twitter_handle)
        if url == feed_url:
            return render_template('add_feed.html', error=_("Feed already exists") + " " + url)

    if twitter_handle:
        return render_template('add_feed.html', twitter_handle=twitter_handle, groups=g.aggregator.get_groups(), bookmarklet=bookmarklet)
    return render_template('add_feed.html', url=url, groups=g.aggregator.get_groups(), bookmarklet=bookmarklet)


@pages_blueprint.route("/item")
@catches_exceptions
@requires_auth
def item_page():
    uid = request.args.get('uid')
    iid = uid.split('-')[0]
    u_index = int(uid.split('-')[1])
    item = g.aggregator.get_item(iid)
    rendered_items = convert_rendered_item(item)
    for rendered_item in rendered_items:
        add_image_ui_extras(rendered_item)
    return render_template(
        'item.html',
        item=rendered_items[0],
        items=rendered_items,
        u_index=u_index,
        is_pocket_available=is_pocket_available(),
        is_instapaper_available=is_instapaper_available()
    )


@pages_blueprint.route("/debug")
@catches_exceptions
@requires_auth
def debug_page():
    return render_template('debug.html')
