import os

import pytest
from PIL import Image
from flask import abort
from flask.testing import FlaskClient

from app import create_app
from app.calculations.models import DummyModel

APP_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
TEST_RESOURCES_DIR = os.path.join(APP_DIR, 'tests/resources')


@pytest.fixture()
def configuration():
    config = {
        'ALLOWED_EXTENSIONS': ['.png', '.jpg', '.jpeg', '.gif'],
        'TESTING': True,
        'LOGIN_REQUIRED': False,
        'RESULTS_PER_PAGE': 5,
        'MAX_WRAPPERS_PER_RESULT': 5,
        'MODEL_CONFIG_FILE': os.path.join(APP_DIR, 'config/models/dummy/config.yaml'),
        'CACHE_SIZE': 2,
        'MAX_CONTENT_LENGTH': 10 * 1024 * 1024,
        'META_DATA_DIR': os.path.join(APP_DIR, 'data/demo_data'),
        'MAX_CHARS_TEXT_FILTER': 500
    }
    return config


@pytest.fixture()
def app(configuration):
    app = create_app(configuration)

    app.route('/generate_non_http_exception')(test_generate_non_http_exception)
    app.route('/generate_http_exception/<status_code>')(test_generate_http_exception)

    with app.app_context():
        yield app


@pytest.fixture()
def app_login(configuration):
    configuration.update({
        'LOGIN_REQUIRED': True,
        'SESSION_PERMANENT': False,
        'SESSION_TYPE': "filesystem"
    })
    app = create_app(configuration)

    with app.app_context():
        yield app


@pytest.fixture()
def client(app):
    return FlaskClient(app)


@pytest.fixture()
def client_login(app_login):
    return FlaskClient(app_login)


def test_generate_non_http_exception():
    raise ValueError


def test_generate_http_exception(status_code: str):
    return abort(int(status_code))


def test_url_map(app):
    print(app.url_map)


@pytest.fixture()
def dummy_model() -> DummyModel:
    return DummyModel(labels=['cobra6', 'cobra7'])


@pytest.fixture()
def test_image() -> Image:
    return Image.new('RGB', (300, 300))


@pytest.fixture()
def test_color_image() -> Image:
    return Image.new('RGB', (300, 300), color=(0, 150, 255))


@pytest.fixture
def snippet_overview() -> Image:
    return Image.open(os.path.join(TEST_RESOURCES_DIR, 'snippet_overview.JPG')).convert('RGB').resize((1200, 1000))
