from flask import (
    Blueprint,
    Response,
    current_app,
    make_response,
    render_template,
    send_file,
    send_from_directory,
)

from app.utils import get_locale, redirect_to

index_page = Blueprint('index', __name__, template_folder='templates')


@index_page.route('/')
@index_page.route('/index')
def show():
    return render_template(
        'index.html',
        allowed_extensions=current_app.config['ALLOWED_EXTENSIONS'],
        max_upload_size=current_app.config['MAX_CONTENT_LENGTH'],
        max_chars_text_filter=current_app.config['MAX_CHARS_TEXT_FILTER'],
        languages=current_app.config['LANGUAGES'],
        current_locale=get_locale().upper(),
    )


@index_page.route('/.well-known/security.txt', methods=['GET'])
def security():
    return send_from_directory('.well-known/', 'security.txt')


@index_page.route('/favicon.ico')
def favicon():
    return send_file('static/icons/favicon.ico', mimetype="image/x-icon")


@index_page.route('/locale=<locale>')
def set_locale(locale: str = None) -> Response:
    """
    Set the locale cookie of the user to the given locale if the locale is one of the keys in the
    LANGUAGES app configuration.
    Uses a redirect to 'index', because:
     - Calling make_response(show()) will load the page before the locale is set.
     - Not redirecting to an existing page will lead to an empty page being shown.

    :param locale: The locale chosen by the user.
    :return: Response object with the locale cookie set (if valid) and a redirect to the index page.
    """
    response = make_response(redirect_to('index'))
    if locale in current_app.config['LANGUAGES'].keys():
        response.set_cookie('locale', locale)
    return response
