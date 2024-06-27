from flask import request, Response, g, Blueprint
from galerie.feed_filter import FeedFilter
from .helpers import requires_auth, catches_exceptions, compute_after_for_maybe_today


actions_blueprint = Blueprint('actions', __name__,)


@actions_blueprint.route('/mark_as_read', methods=['POST'])
@requires_auth
@catches_exceptions
def mark_as_read():
    if g.aggregator.supports_mark_items_as_read_by_iid_ascending_and_feed_filter():
        count = g.aggregator.mark_items_as_read_by_iid_ascending_and_feed_filter(
            request.args.get('to_iid'),
            FeedFilter(
                compute_after_for_maybe_today(),
                request.args.get('group')
            ))
    if g.aggregator.supports_mark_items_as_read_by_group_id():
        g.aggregator.mark_items_as_read_by_group_id(request.args.get('group'))
        count = 1

    resp = Response(f'Marked {count} items as read')
    resp.headers['HX-Refresh'] = "true"
    return resp
