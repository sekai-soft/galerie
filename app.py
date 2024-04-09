import os
from dotenv import load_dotenv
from urllib.parse import unquote
from flask import Flask, request, url_for
from pocket import Pocket
from rss_waterfall.images import get_images
from rss_waterfall_web.index import render_index, render_images_html, render_button_html


def get_env_or_bust(key: str) -> str:
    if key not in os.environ:
        raise ValueError(f"Missing required environment variable: {key}")
    return os.environ[key]

load_dotenv()
fever_endpoint = get_env_or_bust('FEVER_ENDPOINT')
fever_username = get_env_or_bust('FEVER_USERNAME')
fever_password = get_env_or_bust('FEVER_PASSWORD')
pocket_client = None
if 'POCKET_CONSUMER_KEY' in os.environ and 'POCKET_ACCESS_TOKEN' in os.environ:
    pocket_consumer_key = os.getenv('POCKET_CONSUMER_KEY')
    pocket_access_token = os.getenv('POCKET_ACCESS_TOKEN')
    pocket_client = Pocket(pocket_consumer_key, pocket_access_token)
max_images = int(os.getenv('MAX_IMAGES', '15'))

app = Flask(__name__, static_url_path='/static')


@app.route("/")
def index():
    all_images = get_images(fever_endpoint, fever_username, fever_password)
    return render_index(
        all_images,
        max_images, 
        url_for('static', filename='style.css'),
        url_for('static', filename='script.js'),
        pocket_client is not None)


@app.route('/motto')
def motto():
    max_uid = request.args.get('max_uid')
    all_images = get_images(fever_endpoint, fever_username, fever_password)
    max_uid_index = -1
    for i, image in enumerate(all_images):
        if image.uid == max_uid:
            max_uid_index = i
            break
    remaining_images = all_images[max_uid_index + 1:]
    return render_images_html(remaining_images, max_images, pocket_client is not None) + render_button_html(remaining_images, max_images)


@app.route('/suki', methods=['POST'])
def suki():
    if not pocket_client:
        return 'Pocket was not configured how did you get here?'
    encoded_url = request.args.get('url')
    url = unquote(encoded_url)
    pocket_client.add(url)
    return f'Added {url} to Pocket'
