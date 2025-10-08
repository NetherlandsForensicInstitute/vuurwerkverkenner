import pathlib
from collections import Counter
from collections.abc import Sequence

from flask import Blueprint, abort, current_app, jsonify, render_template, request, send_from_directory
from flask_babel import gettext
from flask_paginate import Pagination

from app.blueprints.results.pagination import create_navigation
from app.calculations import get_search_results
from app.calculations.cache import add_to_cache, get_from_cache
from app.calculations.core import Result
from app.requests.messages import NO_MATCH_FOUND, RESULTS_NOT_AVAILABLE, RESULTS_NOT_AVAILABLE_FOR_PAGE
from app.requests.validate import (
    process_get_request_article_page,
    process_get_request_category_page,
    process_get_request_results_page,
    process_post_request,
)
from config.render.endangerment_mapping import ENDANGERMENT_MAPPING
from config.render.meta_data_mapping import META_DATA_KEY_MAPPING

results_page = Blueprint('results', __name__, template_folder='templates')


@results_page.route('/search', methods=['POST'])
def run_model():
    """
    Run the model to generate search results for a given image and store these in cache.
    :return: The id of the cached results.
    """
    # process post request and verify its content
    processed_post_request = process_post_request(request)
    errors = processed_post_request.errors
    if not errors:
        results, search_errors = get_search_results(
            processed_post_request.image_data,
            processed_post_request.query_text,
            processed_post_request.text_filter,
            processed_post_request.include_digits,
        )
        errors += search_errors

    if len(errors) > 0:
        # convert to strings, so that join operation works since it does not accept babel lazystrings
        string_errors = [str(error) for error in errors]
        return jsonify(errors=",".join(string_errors))
    if not results:
        return jsonify(errors=NO_MATCH_FOUND)

    return jsonify(results_id=add_to_cache(results))


def _group_results_by_category(results: Sequence[Result]) -> list[Result]:
    """Group the results by category. If there are multiple labels per category, show only the first one."""
    results_by_category = []
    category_set = set()
    for result in results:
        if result.category not in category_set:
            results_by_category.append(result)
            category_set.add(result.category)
    return results_by_category


@results_page.route('/search/results', methods=['GET'])
def show_search_results_page():
    """
    Route for the showing the search results based on the uploaded photo and/or the supplied text.

    :return: The results cached with a certain id
    """
    results_per_page = current_app.config['RESULTS_PER_PAGE']

    processed_get_request = process_get_request_results_page(request)
    errors = processed_get_request.errors
    page = processed_get_request.page
    results = None
    counts = None

    if not errors:
        results = get_from_cache(processed_get_request.results_id)

        if not results:
            errors.append(RESULTS_NOT_AVAILABLE)
        else:
            counts = Counter(r.category for r in results)
            results = _group_results_by_category(results)
            if not results:
                errors.append(NO_MATCH_FOUND)
            elif page <= 0 or len(results) <= (page - 1) * results_per_page:
                errors.append(RESULTS_NOT_AVAILABLE_FOR_PAGE)

    if errors:
        return render_template("results.html", errors=errors)

    # get results for current page
    start = (page - 1) * results_per_page
    end = min(start + results_per_page, len(results))
    page_results = results[start:end]

    # retrieve the first wrapper image and number of articles of every group
    page_results = [
        Result(
            category=r.category,
            label=r.label,
            meta=current_app.meta_data[r.category][r.label]['wrappers'] | {'n_articles': counts[r.category]},
        )
        for r in page_results
    ]

    pagination = Pagination(
        page=page,
        total=len(results),
        search=False,
        record_name=gettext('resultaten'),
        display_msg=gettext("<b>{start} - {end}</b> van <b>{total}</b> {record_name}"),
        per_page=results_per_page,
        href='javascript:retrieveResults({0})',
        inner_window=1,
        outer_window=0,
    )

    return render_template(
        "results.html",
        results=page_results,
        pagination=pagination,
        navigation_links=create_navigation(pagination),
        errors=None,
    )


@results_page.route('/categories/<category>', methods=['GET'])
def show_category_page(category: str):
    """Show the wrappers within a firework category."""
    articles = None
    results_per_page = current_app.config['MAX_WRAPPERS_PER_PAGE']

    processed_get_request = process_get_request_category_page(request, category)
    errors = processed_get_request.errors
    page = processed_get_request.page
    category = processed_get_request.category
    results_id = processed_get_request.results_id

    if not errors:
        articles = current_app.meta_data.get(category)
        if not articles:
            errors.append(RESULTS_NOT_AVAILABLE)
        elif page <= 0 or len(articles) <= (page - 1) * results_per_page:
            errors.append(RESULTS_NOT_AVAILABLE_FOR_PAGE)

    if errors:
        return render_template("category.html", errors=errors)

    # sort articles based on cached predictions
    if cached_predictions := get_from_cache(results_id):
        articles = {
            result.label: articles[result.label] for result in cached_predictions if result.category == category
        }

    # get results for current page
    start = (page - 1) * results_per_page
    end = min(start + results_per_page, len(articles))

    page_results = [
        Result(
            category=category,
            label=key,
            meta={
                'image': articles[key]['wrappers']['image'],
                'article_name': articles[key]['wrappers']['article_name'],
                'label': key,
            },
        )
        for key in list(articles)[start:end]
    ]

    pagination = Pagination(
        page=page,
        total=len(articles),
        search=False,
        record_name=gettext('artikelen in categorie'),
        display_msg=gettext('<b>{start} - {end}</b> van <b>{total}</b> {record_name}'),
        per_page=results_per_page,
        href='javascript:getCategoryData(\'' + category + '\',{0})',
        inner_window=1,
        outer_window=0,
    )

    return render_template(
        "category.html",
        category=category,
        results=page_results,
        pagination=pagination,
        navigation_links=create_navigation(pagination),
        errors=None,
    )


@results_page.route('/categories/<category>/articles/<label>', methods=['GET'])
def show_article_page(category: str, label: str):
    """Show a single firework article for a category and label."""
    processed_get_request = process_get_request_article_page(category, label)
    errors = processed_get_request.errors
    category = processed_get_request.category
    label = processed_get_request.label

    if errors:
        return render_template("article.html", errors=errors)

    article = current_app.meta_data[category][label]['wrappers']
    return render_template(
        "article.html",
        article=article,
        meta_data_key_mapping=META_DATA_KEY_MAPPING,
        endangerment_mapping=ENDANGERMENT_MAPPING,
        errors=None,
    )


@results_page.route('/images/<path:filename>')
def show_image(filename: str):
    """Show the image of a specific firework wrapper."""
    if meta_data_dir := current_app.config.get("REFERENCE_DATA_DIR", None):
        if pathlib.Path(filename).suffix in current_app.config["ALLOWED_EXTENSIONS"]:
            return send_from_directory(meta_data_dir, filename)
    return abort(404)
