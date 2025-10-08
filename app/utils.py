from flask import Response, current_app, redirect, request, url_for
from huggingface_hub.hf_api import HfApi


def redirect_to(page: str) -> Response:
    """Redirect to page by looking up <page>.show."""
    return redirect(url_for(f"{page}.show"))


def get_locale() -> str:
    """
    Look for locale in cookies. Default to BABEL_DEFAULT_LOCALE.
    :return: Locale code, e.g. 'nl' or 'en'.
    """
    lang_code = current_app.config['BABEL_DEFAULT_LOCALE']
    if request.cookies.get('locale'):
        lang_code = request.cookies.get('locale')
    return lang_code


def get_commit_hash_model(repo_id: str) -> str:
    """Get the commit hash of the main branch of the model in `repo_id`."""
    api = HfApi()
    return api.repo_info(repo_id=repo_id, repo_type='model', revision='main').sha[:7]


def get_commit_hash_data(repo_id: str) -> str:
    """Get the commit hash of the main branch of the dataset in `repo_id`."""
    api = HfApi()
    return api.repo_info(repo_id=repo_id, repo_type='dataset', revision='main').sha[:7]
