import os
import base64
import sentry_sdk
import click
from dotenv import load_dotenv
from flask import Flask, request
from flask_babel import Babel
from galerie_flask.actions_blueprint import actions_blueprint
from galerie_flask.pages_blueprint import pages_blueprint

load_dotenv()

if os.getenv('SENTRY_DSN'):
    sentry_sdk.init(
        dsn=os.getenv('SENTRY_DSN'),
    )


def get_locale():
    return request.accept_languages.best_match(['en', 'zh']) 

app = Flask(__name__, static_url_path='/static')
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config["BABEL_TRANSLATION_DIRECTORIES"] = os.path.join(
    os.path.abspath(os.path.dirname(__file__)),
    "galerie_flask",
    "translations")
babel = Babel(app, locale_selector=get_locale)
app.register_blueprint(pages_blueprint, url_prefix='/')
app.register_blueprint(actions_blueprint, url_prefix='/actions')


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


image_loading_svg_base64 = read_svg_as_base64('static/image-loading.svg')
image_error_svg_base64 = read_svg_as_base64('static/image-error.svg')


@app.context_processor
def inject_svg_base64():
    return dict(
        image_loading_svg_base64=image_loading_svg_base64,
        image_error_svg_base64=image_error_svg_base64
    )
