from flask import Blueprint, render_template, g, request
from flask_babel import _
from galerie.rendered_item import convert_rendered_item
from galerie.twitter import extract_twitter_handle_from_feed_url, extract_twitter_handle_from_url, create_nitter_feed_url
from galerie_flask.pages_blueprint import catches_exceptions, requires_auth
from galerie_flask.instapaper import is_instapaper_available


item_bp = Blueprint('item', __name__, template_folder='.')


@item_bp.route("/item")
@catches_exceptions
@requires_auth
def item():
    uid = request.args.get('uid')
    iid = uid.split('-')[0]
    u_index = int(uid.split('-')[1])

    item = g.aggregator.get_item(iid)
    rendered_items = convert_rendered_item(item, ignore_rendered_items_cap=True)
    feed_icon = g.aggregator.get_feed_icon(item.fid)

    rt = None
    rt_feed = None
    rt_feed_icon = None

    item_url = item.url
    item_url_twitter_handle = extract_twitter_handle_from_url(item_url)
    if item_url_twitter_handle:
        feed = g.aggregator.get_feed(item.fid)
        feed_url = feed.features["feed_url"]
        feed_url_twitter_handle = extract_twitter_handle_from_feed_url(feed_url)
        if feed_url_twitter_handle and feed_url_twitter_handle != item_url_twitter_handle:
            rt = item_url_twitter_handle
            rt_feed = g.aggregator.find_feed_by_feed_url(create_nitter_feed_url(item_url_twitter_handle))
            if rt_feed:
                rt_feed_icon = g.aggregator.get_feed_icon(rt_feed.fid)

    return render_template(
        'item.html',
        feed_icon=feed_icon,
        rt=rt,
        rt_feed=rt_feed,
        rt_feed_icon=rt_feed_icon,
        item=rendered_items[0],
        items=rendered_items,
        u_index=u_index,
        is_instapaper_available=is_instapaper_available()
    )
