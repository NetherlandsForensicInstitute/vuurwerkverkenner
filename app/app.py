import gzip
import json
import logging
import os
from pathlib import Path
from types import MappingProxyType
from typing import Any, Iterable, Mapping, Optional, Union

import confidence
import numpy as np
from flask import Flask, Response
from lru import LRU
from werkzeug.exceptions import HTTPException

from app.blueprints.help import help
from app.blueprints.index import index
from app.blueprints.login import login
from app.blueprints.results import results
from app.blueprints.utils import redirect_to
from app.calculations.models import ClassificationModel, load_model
from app.requests.validate import clean_text

APP_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))


def get_model(app_config: Mapping[str, Any]) -> ClassificationModel:
    config = confidence.loadf(app_config['MODEL_CONFIG_FILE'])
    model = load_model(config.model)
    if not isinstance(model, ClassificationModel):
        raise ValueError('Classification model needed for prediction')
    return model


def build_image_url(label: str, wrapper_index: int, filename: str) -> str:
    return f'fireworks_{label}/wrappers/{wrapper_index}/{filename}'


def parse_json(filename: str) -> Mapping[str, Any]:
    if filename.endswith('.gz'):
        fh = gzip.open
    else:
        fh = open
    with fh(filename, 'r') as f:
        return json.loads(f.read())


def parse_meta_data(meta_data_dir: str, key_order: Optional[Iterable] = None) -> Mapping[str, Any]:
    """
    Parse and return the fireworks meta-data from the meta-data directory.

    :param meta_data_dir: the directory to parse the meta-data from.
        It is assumed that the gzip-compressed JSON containing all the meta-data is
        located in the root of this directory and has the filename "meta.json.gz".
        It is also assumed that the JSON file follows the same structure as in the
        example JSON that can be found in "data/demo_data/meta.json.gz"
    :param key_order: optional parameter for defining the insertion order of the
        meta-data keys. This defines the order in which the meta-data fields will be
        displayed on the page

    :returns: an immutable mapping containing all the parsed meta-data
    """
    filename = os.path.join(meta_data_dir, 'meta.json.gz')
    meta_data = parse_json(filename=filename)
    for label, group in meta_data.items():
        for i, item in group["wrappers"].items():
            # insert the keys in order of `key_order` if defined
            if key_order:
                item_sorted = {key: item[key] for key in key_order if key in item}
                item_sorted.update({key: item[key] for key in item if key not in item_sorted})
                item = item_sorted
            # clean the wrapper text
            item["text"] = clean_text(item["text"])
            # retrieve the image location for the wrapper
            item["image"] = build_image_url(label, i, 'wrapper.jpg')
            images = os.listdir(os.path.join(meta_data_dir, f'fireworks_{label}', 'wrappers', str(i)))
            item["meta_images"] = tuple(build_image_url(label, i, img) for img in images if img != 'wrapper.jpg')
            # overwrite entry
            group["wrappers"][i] = item
        # convert the embeddings to numpy arrays
        group["embeddings"] = np.asarray(group["embeddings"])
    return MappingProxyType(meta_data)


def parse_mapping(filename: str) -> Mapping[str, str]:
    filename = os.path.join(APP_DIR, 'config', 'render', filename)
    return MappingProxyType(parse_json(filename=filename))


def create_app(config: Union[str, Mapping[str, Any]] = 'setup.cfg'):
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

    app.register_blueprint(index.index_page)
    app.register_blueprint(help.help_page)
    app.register_blueprint(results.results_page)

    app.meta_data_key_mapping = parse_mapping('meta_data_key_mapping.json')
    app.endangerment_mapping = parse_mapping('endangerment_mapping.json')

    if meta_data_dir := app.config.get("META_DATA_DIR", None):
        # change relative path to absolute path if necessary
        if not os.path.isabs(meta_data_dir):
            app.config['META_DATA_DIR'] = str(Path().absolute() / Path(meta_data_dir))
        app.meta_data = parse_meta_data(meta_data_dir=app.config['META_DATA_DIR'],
                                        key_order=app.meta_data_key_mapping.keys())
    else:
        app.meta_data = {}

    app.model = get_model(app.config)
    app.cache = LRU(app.config.get('CACHE_SIZE'))
    app.jinja_env.filters['zip'] = zip

    register_error_handlers(app)

    app.after_request(after_request)

    if app.config.get("LOGIN_REQUIRED", None):
        app.register_blueprint(login.login_page)
        from flask_session import Session
        Session(app)

    return app


def register_error_handlers(app):
    app.register_error_handler(404, redirect_bad_request)
    app.register_error_handler(405, redirect_bad_request)
    app.register_error_handler(Exception, handle_exception)


def redirect_bad_request(ex: Exception):
    logging.error(f"Bad request received (will be ignored with a redirect to the index page): {ex}")
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
    response.headers['Content-Security-Policy'] = "default-src 'none';" \
                                                  "img-src 'self' data:;" \
                                                  "font-src 'self';" \
                                                  "connect-src 'self';" \
                                                  "script-src 'self' 'unsafe-inline';" \
                                                  "style-src 'self' 'unsafe-inline';" \
                                                  "form-action 'self'; "
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    return response
