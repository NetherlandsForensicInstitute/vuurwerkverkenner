import os

from flask import Blueprint, current_app, render_template

from app.blueprints.help.resources.help import get_faq

RESOURCES_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'resources')
help_page = Blueprint('help', __name__, template_folder='templates')


def _render_help_page():
    return render_template('help.html', json_data=get_faq(current_app))


@help_page.route('/help')
def show():
    return _render_help_page()
