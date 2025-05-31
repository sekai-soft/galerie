import os
import base64
import sentry_sdk
import click
import datetime
from dotenv import load_dotenv
from flask import Flask, request
from flask_babel import Babel
from flask_static_digest import FlaskStaticDigest
from galerie_flask.db import db
from galerie_flask.actions_blueprint import actions_blueprint
from galerie_flask.pages_blueprint import pages_blueprint
from galerie_flask.actions.actions_routes import actions_bp
from galerie_flask.pages.routes import pages_bp


load_dotenv()

if 'SENTRY_DSN' in os.environ:
    sentry_sdk.init(dsn=os.environ['SENTRY_DSN'])


def get_locale():
    return request.accept_languages.best_match(['en', 'zh']) 


app = Flask(__name__, static_url_path='/static')
app.config['TEMPLATES_AUTO_RELOAD'] = True

if 'SQLALCHEMY_DATABASE_URI' in os.environ:
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ['SQLALCHEMY_DATABASE_URI']

app.config["BABEL_TRANSLATION_DIRECTORIES"] = os.path.join(
    os.path.abspath(os.path.dirname(__file__)),
    "galerie_flask",
    "translations"
)
babel = Babel(app, locale_selector=get_locale)

flask_static_digest = FlaskStaticDigest()
flask_static_digest.init_app(app)

app.register_blueprint(pages_blueprint, url_prefix='/')
app.register_blueprint(actions_blueprint, url_prefix='/actions')
app.register_blueprint(pages_bp, url_prefix='/')
app.register_blueprint(actions_bp, url_prefix='/actions')


if 'SQLALCHEMY_DATABASE_URI' in os.environ:
    db.init_app(app)
    with app.app_context():
        db.create_all()


@app.template_filter('format_count')
def format_count(count: int) -> str:
    if count is None:
        return "0"
    if count >= 1000:
        k = count // 1000
        h = (count - k * 1000) // 100
        if h == 0:
            return f"{k}k"
        return f"{k}.{h}k"
    return str(count)


@app.template_filter('time_ago')
def time_ago(dt) -> str:
    try:
        diff = datetime.datetime.now() - dt
        seconds = diff.total_seconds()

        if seconds < 60:
            return "Just now"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            return f"{minutes} {'minute' if minutes == 1 else 'minutes'} ago"
        elif seconds < 86400:
            hours = int(seconds // 3600)
            return f"{hours} {'hour' if hours == 1 else 'hours'} ago"
        elif seconds < 2592000:  # ~30 days
            days = int(seconds // 86400)
            return f"{days} {'day' if days == 1 else 'days'} ago"
        elif seconds < 31536000:  # ~365 days
            months = int(seconds // 2592000)
            return f"{months} {'month' if months == 1 else 'months'} ago"
        else:
            years = int(seconds // 31536000)
            return f"{years} {'year' if years == 1 else 'years'} ago"
    except Exception:
        return ""


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


def read_svg_as_base64(filepath):
    with open(filepath, 'r') as file:
        svg_content = file.read()
    return base64.b64encode(svg_content.encode('utf-8')).decode('utf-8')


image_loading_svg_base64 = read_svg_as_base64('static/image_loading.svg')
image_error_svg_base64 = read_svg_as_base64('static/image_error.svg')


@app.context_processor
def inject():
    injects = {
        'image_loading_svg_base64': image_loading_svg_base64,
        'image_error_svg_base64': image_error_svg_base64,
    }

    if 'SENTRY_DSN' in os.environ:
        injects['sentry_dsn'] = os.environ['SENTRY_DSN']

    return injects
