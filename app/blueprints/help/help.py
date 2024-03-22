import json
import os
from functools import lru_cache

from flask import Blueprint, render_template

from app.blueprints.login import verify_authorization

RESOURCES_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'resources')
help_page = Blueprint('help', __name__, template_folder='templates')


def _parse_json_data(filename: str):
    with open(filename, 'r') as f:
        return json.loads(f.read())


@lru_cache(maxsize=None)
def _render_help_page():
    json_data = _parse_json_data(filename=os.path.join(RESOURCES_DIR, 'help.json'))
    return render_template('help.html', json_data=json_data)


@help_page.route('/help')
@verify_authorization
def show():
    return _render_help_page()
