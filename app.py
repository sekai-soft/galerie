import os
import base64
import json
from functools import wraps
from dotenv import load_dotenv
from urllib.parse import unquote, unquote_plus
from flask import Flask, request, url_for, Response, g, redirect, make_response
from pocket import Pocket
from rss_waterfall.fever import mark_items_as_read, fever_auth, FeverAuthError
from rss_waterfall.images import get_images, uid_to_item_id
from rss_waterfall_web.index import render_index, render_images_html, render_button_html
from rss_waterfall_web.login import render_login

app = Flask(__name__, static_url_path='/static')
load_dotenv()


def load_fever_auth():
    env_endpoint = os.getenv('FEVER_ENDPOINT')
    env_username = os.getenv('FEVER_USERNAME')
    env_password = os.getenv('FEVER_PASSWORD')
    if env_endpoint and env_username and env_password:
        return env_endpoint, env_username, env_password

    auth_cookie = request.cookies.get('auth')
    if not auth_cookie:
        return False
    auth = base64.b64decode(auth_cookie).decode('utf-8')
    auth = json.loads(auth)
    cookie_endpoint = auth.get('endpoint')
    cookie_username = auth.get('username')
    cookie_password = auth.get('password')
    if cookie_endpoint and cookie_username and cookie_password:
        return cookie_endpoint, cookie_username, cookie_password

    return False


def requires_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        fever_auth = load_fever_auth()
        if not fever_auth:
            return redirect('/login')
        g.fever_endpoint, g.fever_username, g.fever_password = fever_auth
        return f(*args, **kwargs)
    return decorated_function


pocket_client = None
if 'POCKET_CONSUMER_KEY' in os.environ and 'POCKET_ACCESS_TOKEN' in os.environ:
    pocket_consumer_key = os.getenv('POCKET_CONSUMER_KEY')
    pocket_access_token = os.getenv('POCKET_ACCESS_TOKEN')
    pocket_client = Pocket(pocket_consumer_key, pocket_access_token)

max_images = int(os.getenv('MAX_IMAGES', '15'))


@app.route("/login")
def login():
    fever_auth = load_fever_auth()
    if fever_auth:
        return redirect('/')
    return render_login(
        url_for('static', filename='style.css'),
        request.accept_languages.best_match(['en', 'zh']))

I18N = {
    "zh": {
        "Failed to authenticate with Fever API": "无法登陆 Fever API",
        "Unknown server error": "未知服务器错误",
    }
}


def get_string(en_string: str, lang: str) -> str:
    return I18N.get(lang, {}).get(en_string, en_string)


@app.route('/auth', methods=['POST'])
def auth():
    lang = request.accept_languages.best_match(['en', 'zh'])
    endpoint = request.form.get('endpoint')
    username = request.form.get('username')
    password = request.form.get('password')
    try:
        fever_auth(endpoint, username, password)
        resp = make_response()
        auth_str = json.dumps({
            'endpoint': endpoint,
            'username': username,
            'password': password
        })
        auth_bytes = auth_str.encode("utf-8")
        b64_auth_bytes = base64.b64encode(auth_bytes)
        resp.set_cookie('auth', b64_auth_bytes.decode('utf-8'))
        resp.headers['HX-Redirect'] = '/'
        return resp
    except FeverAuthError:
        resp =  make_response()
        resp.status_code = 401
        resp.headers['HX-Trigger'] = json.dumps({"showMessage": get_string("Failed to authenticate with Fever API", lang)})
        return resp
    except Exception as e:
        resp =  make_response()
        resp.status_code = 500
        resp.headers['HX-Trigger'] = json.dumps({"showMessage": f"{get_string("Unknown server error", lang)}\n{str(e)}"})
        return resp


@app.route("/deauth", methods=['POST'])
def deauth():
    resp = make_response()
    resp.delete_cookie('auth')
    resp.headers['HX-Redirect'] = '/login'
    return resp


@app.route("/")
@requires_auth
def index():
    all_images = get_images(g.fever_endpoint, g.fever_username, g.fever_password)
    return render_index(
        all_images,
        max_images, 
        url_for('static', filename='style.css'),
        url_for('static', filename='script.js'),
        pocket_client is not None,
        request.cookies.get('auth') is not None,
        request.accept_languages.best_match(['en', 'zh']))


@app.route('/motto')
@requires_auth
def motto():
    max_uid = request.args.get('max_uid')
    session_max_uid = request.args.get('session_max_uid')
    all_images = get_images(g.fever_endpoint, g.fever_username, g.fever_password)
    max_uid_index = -1
    for i, image in enumerate(all_images):
        if image.uid == max_uid:
            max_uid_index = i
            break
    remaining_images = all_images[max_uid_index + 1:]
    return render_images_html(remaining_images, max_images, pocket_client is not None) + \
        render_button_html(remaining_images, max_images, session_max_uid, request.accept_languages.best_match(['en', 'zh']))


@app.route('/suki', methods=['POST'])
def suki():
    if not pocket_client:
        return 'Pocket was not configured. How did you get here?'
    encoded_url = request.args.get('url')
    url = unquote(encoded_url)
    encoded_tags = request.args.getlist('tag')
    tags = list(map(unquote_plus, encoded_tags))
    pocket_client.add(url, tags=tags)
    return f'Added {url} to Pocket'


@app.route('/owari', methods=['POST'])
@requires_auth
def owari():
    session_max_uid = request.args.get('session_max_uid')
    min_uid = request.args.get('min_uid')
    max_item_id = uid_to_item_id(session_max_uid)
    min_item_id = uid_to_item_id(min_uid)
    
    mark_as_read_item_ids = []
    all_images = get_images(g.fever_endpoint, g.fever_username, g.fever_password)
    for image in all_images:
        item_id = uid_to_item_id(image.uid)
        if min_item_id <= item_id <= max_item_id:
            mark_as_read_item_ids.append(item_id)
    mark_items_as_read(g.fever_endpoint, g.fever_username, g.fever_password, mark_as_read_item_ids)
    resp = Response(f'Marked {len(mark_as_read_item_ids)} items as read')
    resp.headers['HX-Refresh'] = "true"
    return resp
