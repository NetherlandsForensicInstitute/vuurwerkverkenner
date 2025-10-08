import gzip
import json
import logging
import os
import re
from collections.abc import Mapping
from datetime import datetime
from pathlib import Path
from types import MappingProxyType
from typing import Any

import numpy as np
from flask import Flask, Response, request
from flask_babel import Babel
from huggingface_hub import snapshot_download
from lru import LRU
from speaklater import make_lazy_string
from werkzeug.exceptions import HTTPException

from app.blueprints.help import help
from app.blueprints.index import index
from app.blueprints.results import results
from app.calculations.models import EmbeddingClassifier, ViTEmbeddingModel, ViTModelConfig
from app.requests.validate import clean_text
from app.utils import get_locale, redirect_to
from config.render.meta_data_mapping import (
    META_DATA_KEY_MAPPING,
    META_DATA_VALUE_MAPPING_STRING,
    META_DATA_VALUE_MAPPING_WORDS,
)

APP_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))


def get_model(model_name: str, checkpoint_dir: str, meta_data: Mapping[str, Any]) -> EmbeddingClassifier:
    snapshot_download(repo_id=model_name, local_dir=checkpoint_dir)

    with open(os.path.join(checkpoint_dir, 'settings.json')) as f:
        model_config = json.load(f)

    if backbone := model_config.get("backbone"):
        if backbone == "vit":
            model_config["params"]["device"] = "cpu"
            vit_config = ViTModelConfig(**model_config["params"])
            embedding_model = ViTEmbeddingModel(config=vit_config)
            embedding_model.load(os.path.join(checkpoint_dir, "best_weights.pt"), device="cpu")
        else:
            raise ValueError(f"backbone '{backbone}' not supported")
    else:
        raise ValueError("'backbone' field missing in `settings.json`")

    model = EmbeddingClassifier(model=embedding_model)
    model.update_embeddings(meta_data)

    return model


def build_image_url(category: str, label: str, filename: str) -> str:
    """Build the url to the image."""
    return f'{category}/{label}/{filename}'


def parse_json(filename: str) -> Mapping[str, Any]:
    if filename.endswith('.gz'):
        fh = gzip.open
    else:
        fh = open
    with fh(filename, 'r') as f:
        return json.loads(f.read())


def get_meta_data(app_config: Mapping[str, Any]) -> Mapping[str, Any]:
    """
    Download, parse and return the fireworks meta-data from the meta-data directory. The meta-data should consist of
    a `meta.json.gz` file and nested folders each category/label containing the images.

    :param app_config: Global constants used in the application
    :returns: an immutable mapping containing all the parsed meta-data
    """
    if app_config.get('META_DATA_HF'):
        snapshot_download(
            repo_id=app_config['META_DATA_HF'], repo_type="dataset", local_dir=app_config['META_DATA_DIR']
        )
    meta_data = parse_json(filename=os.path.join(app_config['REFERENCE_DATA_DIR'], 'meta.json.gz'))
    for category, articles in meta_data.items():
        for label, article in articles.items():
            article_meta_data = article.get('wrappers', {})
            # insert the keys in order of `META_DATA_KEY_MAPPING.keys()`
            article_meta_data_sorted = {
                key: article_meta_data[key] for key in META_DATA_KEY_MAPPING.keys() if key in article_meta_data
            }
            article_meta_data_sorted.update(
                {key: article_meta_data[key] for key in article_meta_data if key not in article_meta_data_sorted}
            )
            article_meta_data = article_meta_data_sorted  # noqa
            # clean the wrapper text
            article_meta_data["text"] = clean_text(article_meta_data.get("text", ""))
            # retrieve the image location for the wrapper
            article_meta_data["image"] = build_image_url(category, label, app_config['WRAPPER_FILENAME'])
            images = os.listdir(os.path.join(app_config['REFERENCE_DATA_DIR'], category, label))
            article_meta_data["meta_images"] = tuple(
                build_image_url(category, label, img) for img in images if img != app_config['WRAPPER_FILENAME']
            )
            # overwrite entry
            article["wrappers"] = article_meta_data
            # convert the embeddings to numpy arrays
            article["embeddings"] = np.asarray(article["embeddings"])
    return MappingProxyType(meta_data)


def create_app(config: str | Mapping[str, Any] = 'setup.cfg'):
    """
    Create the app. This method is automatically detected and triggered by Flask.

    :param config: either a filename (str) or a parsed configuration mapping.
        In both cases, the app.config will be updated with the info from the mapping
    """
    app = Flask(__name__)

    if isinstance(config, str):
        app.config.from_pyfile(config)
    else:
        app.config.update(config)

    Babel(app, locale_selector=get_locale)

    app.register_blueprint(index.index_page)
    app.register_blueprint(help.help_page)
    app.register_blueprint(results.results_page)

    if not os.path.isabs(app.config['META_DATA_DIR']):
        app.config['META_DATA_DIR'] = str(Path().absolute() / app.config['META_DATA_DIR'])
    app.config['REFERENCE_DATA_DIR'] = os.path.join(app.config['META_DATA_DIR'], 'reference_data')
    app.meta_data = get_meta_data(app_config=app.config)

    if not os.path.isabs(app.config['MODEL_DIR']):
        app.config['MODEL_DIR'] = str(Path().absolute() / app.config['MODEL_DIR'])
    app.config["MODEL_DIR"] = str(Path().absolute() / Path(app.config['MODEL_DIR']))
    app.model = get_model(app.config.get("MODEL_HF"), app.config["MODEL_DIR"], app.meta_data)
    app.cache = LRU(app.config.get('CACHE_SIZE'))
    app.jinja_env.filters['zip'] = zip
    app.jinja_env.filters['translate_meta_data_values'] = translate_meta_data_values

    register_error_handlers(app)

    app.after_request(after_request)

    return app


def translate_meta_data_values(input: str):
    """
    Translate the parts of the string defined in `META_DATA_VALUE_MAPPING_STRING` and then split the string in words and
    translate individually from `META_DATA_VALUE_MAPPING_WORDS`. Return the translated string as a LazyString.
    """
    # Make the mapping keys lowercase
    smap = {k.lower(): v for k, v in META_DATA_VALUE_MAPPING_STRING.items()}
    wmap = {k.lower(): v for k, v in META_DATA_VALUE_MAPPING_WORDS.items()}

    # Compile the patterns to replace
    sub_pat = re.compile("|".join(map(re.escape, sorted(smap, key=len, reverse=True))), re.IGNORECASE)
    word_pat = re.compile(rf"(?<![A-Za-z0-9])({'|'.join(map(re.escape, wmap))})(?![A-Za-z0-9])", re.IGNORECASE)

    def apply_subs(string: str) -> str:
        string = sub_pat.sub(lambda m: str(smap[m.group(0).lower()]), string)
        string = word_pat.sub(lambda m: str(wmap[m.group(0).lower()]), string)
        return string

    # Apply the substitutions and return as a lazy string
    return make_lazy_string(lambda t: apply_subs(t).capitalize(), input)


def register_error_handlers(app):
    app.register_error_handler(404, redirect_bad_request)
    app.register_error_handler(405, redirect_bad_request)
    app.register_error_handler(Exception, handle_exception)


def redirect_bad_request(ex: Exception):
    logging.error(
        f"{datetime.now()} Bad request received: {request.path} "
        f"(will be ignored with a redirect to the index page): {ex}"
    )
    return redirect_to("index")


def handle_exception(ex: Exception):
    # since an HTTP error is a valid WSGI response, we may directly return the HTTP error
    # (for other than the already registered 404 and 405 status codes, which invoke a redirect to the index page)
    if isinstance(ex, HTTPException):
        return ex

    # redirect non-HTTP exceptions to index page
    return redirect_bad_request(ex)


def after_request(response: Response):
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Content-Security-Policy'] = (
        "default-src 'none';"
        "img-src 'self' data:;"
        "font-src 'self';"
        "connect-src 'self';"
        "script-src 'self' 'unsafe-inline';"
        "style-src 'self' 'unsafe-inline';"
        "form-action 'self'; "
    )
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    return response
