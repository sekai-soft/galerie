from flask import request, Blueprint, g
from flask_babel import _
from galerie.twitter import create_nitter_feed_url, extract_twitter_handle_from_url, get_twitter_handle_from_status_url
from galerie_flask.actions_blueprint import make_toast, make_hx_redirect, catches_exceptions, make_back
from galerie_flask.utils import requires_auth


add_feed_bp = Blueprint('add_feed', __name__)


@add_feed_bp.route('/add_feed', methods=['POST'])
@requires_auth
@catches_exceptions
def add_feed():
    if 'group' not in request.form:
        return make_toast(400, "Group is required")
    gid = request.form.get('group')
    url = request.form['url']

    twitter_handle = extract_twitter_handle_from_url(url)
    if twitter_handle:
        if twitter_handle == 'i':
            twitter_handle = get_twitter_handle_from_status_url(url)
        feed_url = create_nitter_feed_url(twitter_handle)
    else:
        feed_url = url
    if not feed_url:
        return make_toast(400, "URL is required")

    existing_feed = g.aggregator.find_feed_by_url(feed_url)
    if existing_feed:
        return make_toast(200, _('This feed already exists'))

    fid = g.aggregator.add_feed(feed_url, gid)
    if not fid:
        return make_toast(400, _('Unable to detect a valid feed'))

    view_feed = request.args.get('view_feed', '0') == '1'
    if view_feed:
        return make_hx_redirect(f'/feed?fid={fid}')
    
    go_home = request.args.get('go_home', '0') == '1'
    if go_home:
        return make_hx_redirect('/')

    show_toast = request.args.get('show_toast', '0') == '1'
    if show_toast:
        return make_toast(200, _('Feed added'))

    return make_back()
