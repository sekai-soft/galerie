import os
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
