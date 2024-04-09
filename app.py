import os
from dotenv import load_dotenv
from flask import Flask, request, url_for
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
max_images = int(os.getenv('MAX_IMAGES', '15'))

app = Flask(__name__, static_url_path='/static')


@app.route("/")
def index():
    all_images = get_images(fever_endpoint, fever_username, fever_password)
    return render_index(
        all_images,
        max_images, 
        url_for('static', filename='style.css'),
        url_for('static', filename='script.js'))


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
    return render_images_html(remaining_images, max_images) + render_button_html(remaining_images, max_images)
