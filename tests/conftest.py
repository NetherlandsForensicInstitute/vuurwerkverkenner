import io
import os
import urllib

import pytest
from flask import abort
from flask.testing import FlaskClient
from PIL import Image

from app import create_app
from app.app import get_meta_data
from app.calculations.cache import add_to_cache
from app.calculations.core import Result
from app.calculations.models import EmbeddingClassifier, ViTEmbeddingModel, ViTModelConfig

APP_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
TEST_RESOURCES_DIR = os.path.join(APP_DIR, 'tests/resources')


@pytest.fixture
def configuration():
    config = {
        'ALLOWED_EXTENSIONS': ['.png', '.jpg', '.jpeg', '.gif'],
        'TESTING': True,
        'RESULTS_PER_PAGE': 5,
        'MAX_WRAPPERS_PER_PAGE': 5,
        'CACHE_SIZE': 2,
        'MAX_CONTENT_LENGTH': 10 * 1024 * 1024,
        'META_DATA_DIR': os.path.join(APP_DIR, 'tests/resources/demo_data'),
        'MAX_CHARS_TEXT_FILTER': 500,
        'BABEL_DEFAULT_LOCALE': 'nl',
        'LANGUAGES': {"nl": "Nederlands", "en": "English"},
        'WRAPPER_FILENAME': 'wrapper.png',
        'MODEL_DIR': 'data/model',
        'META_DATA_HF': None,
        'REFERENCE_DATA_DIR': os.path.join(APP_DIR, 'tests/resources/demo_data', 'reference_data'),
    }
    return config


@pytest.fixture
def vit_model_test_config() -> ViTModelConfig:
    config = ViTModelConfig(
        model_size="base",
        embedding_size=128,
        image_size=64,
        patch_size=32,
        add_pooling_layer=False,
        mean_pooling=False,
        device="cpu",
        force_download=False,
    )
    return config


@pytest.fixture
def app(mocker, configuration, vit_model_test_config: ViTModelConfig):
    fake_model = EmbeddingClassifier(model=ViTEmbeddingModel(config=vit_model_test_config))
    fake_model.update_embeddings(meta_data=get_meta_data(app_config=configuration))
    mocker.patch('app.app.get_model', return_value=fake_model)
    mocker.patch('app.blueprints.help.resources.help.get_commit_hash_model', return_value='test_hash')
    mocker.patch('app.blueprints.help.resources.help.get_commit_hash_data', return_value='test_hash')
    app = create_app(configuration)

    app.route('/generate_non_http_exception')(test_generate_non_http_exception)
    app.route('/generate_http_exception/<status_code>')(test_generate_http_exception)

    with app.app_context():
        yield app


@pytest.fixture
def client(app):
    return FlaskClient(app)


def test_generate_non_http_exception():
    raise ValueError


def test_generate_http_exception(status_code: str):
    return abort(int(status_code))


def test_url_map(app):
    print(app.url_map)


@pytest.fixture
def test_image() -> Image:
    return Image.new('RGB', (300, 300))


@pytest.fixture
def test_color_image() -> Image:
    return Image.new('RGB', (300, 300), color=(0, 150, 255))


@pytest.fixture
def snippet_overview() -> Image:
    return Image.open(os.path.join(TEST_RESOURCES_DIR, 'snippet_overview.JPG')).convert('RGB').resize((1200, 1000))


@pytest.fixture
def results_id(client: FlaskClient) -> str:
    # Create a result_id with all entries of the reference data as a result
    all_results = []
    for category, category_data in client.application.meta_data.items():
        all_results.extend(Result(category=category, label=label, score=1) for label in category_data)
    all_results = tuple(all_results)

    return add_to_cache(all_results)


def image_post_request_data(query_text: str | None = None, text_filter: str = 'false', include_digits: str = 'false'):
    with open(f'{TEST_RESOURCES_DIR}/snippet_cobra.png', 'rb') as f:
        file_bytes = f.read()
    return post_request_data(
        file=io.BytesIO(file_bytes),
        filename="test.jpg",
        query_text=query_text or '',
        text_filter=text_filter,
        include_digits=include_digits,
    )


def large_image_request_data(file_size: int):
    return {"file": (io.BytesIO(bytearray(os.urandom(file_size))), "test.jpg"), 'text': 'cobra', 'text_filter': 'false'}


def get_request_data(results_id: str, page: int = 1):
    return urllib.parse.urlencode({"resultsId": results_id, "page": page})


def post_request_data(
    file: io.BytesIO | None = None,
    filename: str = "",
    query_text: str = "",
    text_filter: str = 'false',
    include_digits: str = 'false',
):
    return {
        "file": (file, filename),
        "query_text": query_text,
        "text_filter": text_filter,
        "include_digits": include_digits,
    }
