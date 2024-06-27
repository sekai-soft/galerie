import os
import base64
import json
import pytz
import sentry_sdk
import click
from typing import Optional
from datetime import datetime
from functools import wraps
from dotenv import load_dotenv
from flask import Flask, request, url_for, g, redirect, make_response
from flask_babel import Babel
from pocket import Pocket
from sentry_sdk import capture_exception
from galerie.rss_aggregator import AuthError, RssAggregator
from galerie.fever_aggregator import FeverAggregator
from galerie.miniflux_aggregator import MinifluxAggregator
from galerie.image import extract_images
from galerie.feed_filter import FeedFilter
from galerie_web.index import render_index, render_images_html, render_button_html, IndexPageParameters
from galerie_flask.actions_blueprint import actions_blueprint
from galerie_flask.login_blueprint import login_blueprint

load_dotenv()

if os.getenv('SENTRY_DSN'):
    sentry_sdk.init(
        dsn=os.getenv('SENTRY_DSN'),
    )


def get_locale():
    return request.accept_languages.best_match(['en', 'zh']) 

app = Flask(__name__, static_url_path='/static')
app.config["BABEL_TRANSLATION_DIRECTORIES"] = os.path.join(
    os.path.abspath(os.path.dirname(__file__)),
    "galerie_flask",
    "translations")
babel = Babel(app, locale_selector=get_locale)
app.register_blueprint(actions_blueprint, url_prefix='/')
app.register_blueprint(login_blueprint, url_prefix='/')


@app.cli.group()
def translate():
    """Translation and localization commands."""
    pass


@translate.command()
@click.argument('lang')
def init(lang):
    """Initialize a new language."""
    if os.system('pybabel extract -F babel.cfg -k _l -o messages.pot .'):
        raise RuntimeError('extract command failed')
    if os.system(
            'pybabel init -i messages.pot -d galerie_flask/translations -l ' + lang):
        raise RuntimeError('init command failed')
    os.remove('messages.pot')


@translate.command()
def update():
    """Update all languages."""
    if os.system('pybabel extract -F babel.cfg -k _l -o messages.pot .'):
        raise RuntimeError('extract command failed')
    if os.system('pybabel update -i messages.pot -d galerie_flask/translations'):
        raise RuntimeError('update command failed')
    os.remove('messages.pot')


@translate.command()
def compile():
    """Compile all languages."""
    if os.system('pybabel compile -d galerie_flask/translations'):
        raise RuntimeError('compile command failed')


def try_get_miniflux_aggregator() -> Optional[MinifluxAggregator]:
    env_endpoint = os.getenv('MINIFLUX_ENDPOINT')
    env_username = os.getenv('MINIFLUX_USERNAME')
    env_password = os.getenv('MINIFLUX_PASSWORD')
    if env_endpoint and env_username and env_password:
        return MinifluxAggregator(env_endpoint, env_username, env_password)
    return None


def try_get_fever_aggregator(
        logging_in_endpoint: Optional[str] = None,
        logging_in_username: Optional[str] = None,
        logging_in_password: Optional[str] = None) -> Optional[FeverAggregator]:
    env_endpoint = os.getenv('FEVER_ENDPOINT')
    env_username = os.getenv('FEVER_USERNAME')
    env_password = os.getenv('FEVER_PASSWORD')
    if env_endpoint and env_username and env_password:
        return FeverAggregator(env_endpoint, env_username, env_password)

    if logging_in_endpoint and logging_in_username is not None and logging_in_password is not None:
        return FeverAggregator(logging_in_endpoint, logging_in_username, logging_in_password)

    auth_cookie = request.cookies.get('auth')
    if not auth_cookie:
        return None
    auth = base64.b64decode(auth_cookie).decode('utf-8')
    auth = json.loads(auth)
    cookie_endpoint = auth.get('endpoint')
    cookie_username = auth.get('username')
    cookie_password = auth.get('password')
    if cookie_endpoint and cookie_username and cookie_password:
        return FeverAggregator(cookie_endpoint, cookie_username, cookie_password)

    return None


def get_aggregator(
    logging_in_endpoint: Optional[str] = None,
    logging_in_username: Optional[str] = None,
    logging_in_password: Optional[str] = None) -> Optional[RssAggregator]:
    aggregator = try_get_miniflux_aggregator()
    if aggregator:
        return aggregator
    return try_get_fever_aggregator(logging_in_endpoint, logging_in_username, logging_in_password)


def requires_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        aggregator = get_aggregator()
        if not aggregator:
            return redirect('/login')
        g.aggregator = aggregator
        return f(*args, **kwargs)
    return decorated_function


pocket_client = None
if 'POCKET_CONSUMER_KEY' in os.environ and 'POCKET_ACCESS_TOKEN' in os.environ:
    pocket_consumer_key = os.getenv('POCKET_CONSUMER_KEY')
    pocket_access_token = os.getenv('POCKET_ACCESS_TOKEN')
    pocket_client = Pocket(pocket_consumer_key, pocket_access_token)

max_items = int(os.getenv('MAX_IMAGES', '15'))

I18N = {
    "zh": {
        "Failed to authenticate with Fever API": "无法登陆 Fever API",
        "Unknown server error": "未知服务器错误",
    }
}


def get_string(en_string: str, lang: str) -> str:
    return I18N.get(lang, {}).get(en_string, en_string)


def get_lang():
    return request.accept_languages.best_match(['en', 'zh'])


def catches_exceptions(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            if os.getenv('DEBUG', '0') == '1':
                raise e
            capture_exception(e)
            resp = make_response(f"{get_string("Unknown server error", get_lang())}\n{str(e)}")
            resp.status_code = 500
            return resp
    return decorated_function


@app.route('/auth', methods=['POST'])
def auth():
    endpoint = request.form.get('endpoint')
    username = request.form.get('username', '')
    password = request.form.get('password', '')
    try:
        persisted_auth = get_aggregator(
            logging_in_endpoint=endpoint,
            logging_in_username=username,
            logging_in_password=password).persisted_auth()
        auth_bytes = persisted_auth.encode("utf-8")
        b64_auth_bytes = base64.b64encode(auth_bytes)

        resp = make_response()
        resp.set_cookie('auth', b64_auth_bytes.decode('utf-8'))
        resp.headers['HX-Redirect'] = '/'
        return resp
    except AuthError:
        resp = make_response()
        resp.status_code = 401
        resp.headers['HX-Trigger'] = json.dumps({"showMessage": get_string("Failed to authenticate with Fever API", get_lang())})
        return resp
    except Exception as e:
        resp = make_response()
        resp.status_code = 500
        resp.headers['HX-Trigger'] = json.dumps({"showMessage": f"{get_string("Unknown server error", get_lang())}\n{str(e)}"})
        return resp


@app.route("/deauth", methods=['POST'])
def deauth():
    resp = make_response()
    resp.delete_cookie('auth')
    resp.headers['HX-Redirect'] = '/login'
    return resp


def get_start_of_day_in_epoch(iana_timezone: str) -> int:
    dt = datetime.now(pytz.timezone(iana_timezone))
    start_of_day = dt.replace(hour=0, minute=0, second=0, microsecond=0)
    epoch_time = int(start_of_day.timestamp())
    return epoch_time


def compute_after_for_maybe_today() -> Optional[int]:
    if request.args.get('today') != "1":
        return None
    browser_tz = request.cookies.get('tz')
    return get_start_of_day_in_epoch(browser_tz)


@app.route("/")
@requires_auth
@catches_exceptions
def index():
    if not g.aggregator.supports_get_unread_items_by_iid_descending():
        sort_by_desc = False
    else:
        sort_by_desc = request.args.get('sort', 'desc') == 'desc'

    feed_filter = FeedFilter(
        compute_after_for_maybe_today(),
        request.args.get('group'))
    if sort_by_desc:
        unread_items = g.aggregator.get_unread_items_by_iid_descending(
            max_items,
            None,
            feed_filter)
    else:
        unread_items = g.aggregator.get_unread_items_by_iid_ascending(
            max_items,
            None,
            feed_filter)
    unread_count = g.aggregator.get_unread_items_count(feed_filter)
    images = extract_images(unread_items)
    groups = g.aggregator.get_groups()
    selected_group = g.aggregator.get_group(request.args.get('group'))
    return render_index(
        images,
        url_for('static', filename='style.css'),
        url_for('static', filename='favicon.png'),
        url_for('static', filename='script.js'),
        pocket_client is not None,
        request.cookies.get('auth') is not None,
        get_lang(),
        request.args.get('today') == "1",
        groups,
        selected_group,
        unread_count,
        g.aggregator.supports_get_unread_items_by_iid_descending(),
        sort_by_desc,
        g.aggregator.supports_mark_items_as_read_by_iid_ascending_and_feed_filter(),
        g.aggregator.supports_mark_items_as_read_by_group_id())


@app.route('/load_more')
@requires_auth
@catches_exceptions
def load_more():
    if not g.aggregator.supports_get_unread_items_by_iid_descending():
        sort_by_desc = False
    else:
        sort_by_desc = request.args.get('sort', 'desc') == 'desc'

    if sort_by_desc:
        unread_items = g.aggregator.get_unread_items_by_iid_descending(
            max_items,
            request.args.get('from_iid'),
            FeedFilter(
                compute_after_for_maybe_today(),
                request.args.get('group')
            ))
    else:
        unread_items = g.aggregator.get_unread_items_by_iid_ascending(
            max_items,
            request.args.get('from_iid'),
            FeedFilter(
                compute_after_for_maybe_today(),
                request.args.get('group')
            ))
    images = extract_images(unread_items)

    return render_images_html(images, pocket_client is not None) + \
        render_button_html(
            images,
            g.aggregator.supports_mark_items_as_read_by_iid_ascending_and_feed_filter(),
            g.aggregator.supports_mark_items_as_read_by_group_id(),
            IndexPageParameters(
                lang=get_lang(),
                today=request.args.get('today') == "1",
                group_id=request.args.get('group'),
                sort_by_desc=sort_by_desc))
