from uuid import uuid4
from flask import Blueprint, render_template, g, request
from flask_babel import _
from galerie.rendered_item import convert_rendered_item
from galerie.twitter import extract_twitter_handle_from_url
from galerie_flask.pages_blueprint import catches_exceptions, requires_auth
from galerie_flask.utils import DEFAULT_MAX_RENDERED_ITEMS
from galerie_flask.db import db, Session, ItemViewHistory


item_bp = Blueprint('item', __name__, template_folder='.')


@item_bp.route("/item")
@catches_exceptions
@requires_auth
def item():
    no_text_mode = request.cookies.get('no_text_mode', '0') == '1'
    from_history = request.args.get('from_history', '0') == '1'

    uid = request.args.get('uid')
    iid = uid.split('-')[0]
    u_index = int(uid.split('-')[1])

    item, miniflux_entry = g.aggregator.get_item_and_entry_dict(iid)
    rendered_items = convert_rendered_item(item, DEFAULT_MAX_RENDERED_ITEMS, ignore_rendered_items_cap=True)

    if not from_history:
        # Record item view history (skip if from_history=1)
        session_token = request.cookies.get('session_token')
        session = db.session.query(Session).filter_by(uuid=session_token).first()
        user_uuid = session.user_uuid
        view_history = ItemViewHistory(
            uuid=str(uuid4()),
            user_uuid=user_uuid,
            item_uid=uid,
            miniflux_entry=miniflux_entry
        )
        db.session.add(view_history)
        db.session.commit()

    feed_icon = g.aggregator.get_feed_icon(item.fid)

    rt = None
    rt_feed = None
    rt_feed_icon = None

    item_url = item.url
    item_twitter_handle = extract_twitter_handle_from_url(item_url)
    if item_twitter_handle:
        feed = g.aggregator.get_feed(item.fid)
        feed_url = feed.url
        feed_twitter_handle = extract_twitter_handle_from_url(feed_url)
        if feed_twitter_handle and feed_twitter_handle != item_twitter_handle:
            rt = item_twitter_handle
            rt_feed = g.aggregator.find_feed_by_url(item_url)
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
        no_text_mode=no_text_mode
    )
