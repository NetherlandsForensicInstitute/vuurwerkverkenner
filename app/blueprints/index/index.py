from flask import Blueprint, current_app, render_template, send_file, send_from_directory

from app.blueprints.login import verify_authorization

index_page = Blueprint('index', __name__, template_folder='templates')


@index_page.route('/')
@index_page.route('/index')
@verify_authorization
def show():
    return render_template('index.html',
                           allowed_extensions=current_app.config['ALLOWED_EXTENSIONS'],
                           max_upload_size=current_app.config['MAX_CONTENT_LENGTH'],
                           max_chars_text_filter=current_app.config['MAX_CHARS_TEXT_FILTER'])


@index_page.route('/.well-known/security.txt', methods=['GET'])
@verify_authorization
def security():
    return send_from_directory('.well-known/', 'security.txt')


@index_page.route('/favicon.ico')
@verify_authorization
def favicon():
    return send_file('static/icons/favicon.ico', mimetype="image/x-icon")
