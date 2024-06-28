import os
import json
from functools import wraps
from urllib.parse import unquote, unquote_plus
from flask import request, g, Blueprint, make_response
from flask_babel import _, lazy_gettext as _l
from sentry_sdk import capture_exception
from pocket import Pocket
from galerie.feed_filter import FeedFilter
from .helpers import requires_auth, compute_after_for_maybe_today

pocket_client = None
if 'POCKET_CONSUMER_KEY' in os.environ and 'POCKET_ACCESS_TOKEN' in os.environ:
    pocket_consumer_key = os.getenv('POCKET_CONSUMER_KEY')
    pocket_access_token = os.getenv('POCKET_ACCESS_TOKEN')
    pocket_client = Pocket(pocket_consumer_key, pocket_access_token)

actions_blueprint = Blueprint('actions', __name__)


def make_toast(status_code: int, *args, **kwargs):
    resp = make_response()
    resp.headers['HX-Trigger'] = json.dumps({
        "toast": str(_l(*args, **kwargs))
    })
    resp.status_code = status_code
    return resp


def make_refresh():
    resp = make_response()
    resp.headers['HX-Refresh'] = "true"
    return resp


def catches_exceptions(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            if os.getenv('DEBUG', '0') == '1':
                raise e
            capture_exception(e)
            return make_toast(500, "Unknown server error: %(e)s", e=str(e))
    return decorated_function


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

    return make_refresh()


@actions_blueprint.route('/pocket', methods=['POST'])
@catches_exceptions
def pocket():
    if not pocket_client:
        return make_toast(500, "Pocket was not configured")
    encoded_url = request.args.get('url')
    url = unquote(encoded_url)
    encoded_tags = request.args.getlist('tag')
    tags = list(map(unquote_plus, encoded_tags))
    pocket_client.add(url, tags=tags)
    return make_toast(200, 'Added %(url)s to Pocket', url=url)
