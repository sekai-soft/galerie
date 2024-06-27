import os
from urllib.parse import unquote, unquote_plus
from flask import request, g, Blueprint, make_response
from flask_babel import _
from pocket import Pocket
from galerie.feed_filter import FeedFilter
from .helpers import requires_auth, catches_exceptions, compute_after_for_maybe_today, make_toast

pocket_client = None
if 'POCKET_CONSUMER_KEY' in os.environ and 'POCKET_ACCESS_TOKEN' in os.environ:
    pocket_consumer_key = os.getenv('POCKET_CONSUMER_KEY')
    pocket_access_token = os.getenv('POCKET_ACCESS_TOKEN')
    pocket_client = Pocket(pocket_consumer_key, pocket_access_token)

actions_blueprint = Blueprint('actions', __name__)


@actions_blueprint.route('/mark_as_read', methods=['POST'])
@requires_auth
@catches_exceptions
def mark_as_read():
    if g.aggregator.supports_mark_items_as_read_by_iid_ascending_and_feed_filter():
        g.aggregator.mark_items_as_read_by_iid_ascending_and_feed_filter(
            request.args.get('to_iid'),
            FeedFilter(
                compute_after_for_maybe_today(),
                request.args.get('group')
            ))
    if g.aggregator.supports_mark_items_as_read_by_group_id():
        g.aggregator.mark_items_as_read_by_group_id(request.args.get('group'))

    resp = make_response()
    resp.headers['HX-Refresh'] = "true"
    return resp


@actions_blueprint.route('/pocket', methods=['POST'])
def pocket():
    if not pocket_client:
        return make_toast('Added %(url)s to Pocket', url=url)
    encoded_url = request.args.get('url')
    url = unquote(encoded_url)
    encoded_tags = request.args.getlist('tag')
    tags = list(map(unquote_plus, encoded_tags))
    pocket_client.add(url, tags=tags)
    return make_toast('Added %(url)s to Pocket', url=url)
