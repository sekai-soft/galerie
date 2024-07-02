import os
import pytz
from typing import Optional
from functools import wraps
from datetime import datetime
from flask import request, g, redirect
from pocket import Pocket
from .get_aggregator import get_aggregator

max_items = int(os.getenv('MAX_IMAGES', '15'))

pocket_client = None
if 'POCKET_CONSUMER_KEY' in os.environ and 'POCKET_ACCESS_TOKEN' in os.environ:
    pocket_consumer_key = os.getenv('POCKET_CONSUMER_KEY')
    pocket_access_token = os.getenv('POCKET_ACCESS_TOKEN')
    pocket_client = Pocket(pocket_consumer_key, pocket_access_token)


def requires_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        aggregator = get_aggregator()
        if not aggregator:
            return redirect('/login')
        g.aggregator = aggregator
        return f(*args, **kwargs)
    return decorated_function


def compute_after_for_maybe_today() -> Optional[int]:
    if request.args.get('today') != "1":
        return None
    browser_tz = request.cookies.get('tz')
    dt = datetime.now(pytz.timezone(browser_tz))
    start_of_day = dt.replace(hour=0, minute=0, second=0, microsecond=0)
    return int(start_of_day.timestamp())
