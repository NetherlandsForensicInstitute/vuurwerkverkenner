from functools import wraps

from flask import Blueprint, current_app, render_template, request, session

from app.blueprints.utils import redirect_to

login_page = Blueprint('login', __name__, template_folder='templates')


@login_page.route('/login')
def show():
    return render_template('login.html') if new_login_required() else redirect_to('index')


@login_page.route('/login', methods=['POST'])
def form_posted():
    if request.form['password'] == current_app.config["LOGIN_PASSWORD"]:
        session['logged_in'] = True
        return redirect_to('index')
    return redirect_to('login')


def verify_authorization(f):
    @wraps(f)
    def decorated_func(*args, **kwargs):
        return redirect_to('login') if new_login_required() else f(*args, **kwargs)

    return decorated_func


def new_login_required():
    return current_app.config.get('LOGIN_REQUIRED') and not session.get('logged_in', False)
