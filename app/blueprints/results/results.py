import pathlib
from typing import Any, Mapping

from flask import abort, Blueprint, current_app, jsonify, render_template, request, send_from_directory
from flask_paginate import Pagination

from app.blueprints.login import verify_authorization
from app.blueprints.results.pagination import create_navigation
from app.calculations import get_results
from app.calculations.cache import add_to_cache, get_from_cache
from app.calculations.core import Result
from app.requests.messages import NO_MATCH_FOUND, RESULTS_NOT_AVAILABLE, RESULTS_NOT_AVAILABLE_FOR_PAGE
from app.requests.validate import process_get_request_results, process_get_request_group, process_post_request, \
    process_get_request_item

results_page = Blueprint('results', __name__, template_folder='templates')


def _get_info_by_label(label: str) -> Mapping[str, Any]:
    """
    For a firework label, retrieve the first wrapper image and article name and the
    number of items within that group.
    """
    meta = current_app.meta_data.get(label)
    n_items = len(meta['wrappers'])
    wrapper = meta['wrappers']['0']
    wrapper_image = wrapper['image']
    article_name = wrapper['article_name']
    return {'wrapper_image': wrapper_image, 'n_items': n_items, 'article_name': article_name}


@results_page.route('/results', methods=['POST'])
@verify_authorization
def run_model():
    """
    Run the model to generate results (for a certain image and text) and store these in cache
    :return: The id of the cached results
    """

    # process post request and verify its content
    processed_post_request = process_post_request(request)
    errors = processed_post_request.errors
    if len(errors) > 0:
        return jsonify(errors=",".join(errors))

    results = get_results(query_image=processed_post_request.image_data, query_text=processed_post_request.text)
    if not results:
        return jsonify(errors=NO_MATCH_FOUND)

    return jsonify(results_id=add_to_cache(results))


@results_page.route('/results', methods=['GET'])
@verify_authorization
def show_results():
    """
    :return: The results cached with a certain id
    """
    results_per_page = current_app.config['RESULTS_PER_PAGE']

    processed_get_request = process_get_request_results(request)
    errors = processed_get_request.errors
    page = processed_get_request.page
    results = None

    if not errors:
        results = get_from_cache(processed_get_request.results_id)

        if not results:
            errors.append(RESULTS_NOT_AVAILABLE)
        elif page <= 0 or len(results) <= (page - 1) * results_per_page:
            errors.append(RESULTS_NOT_AVAILABLE_FOR_PAGE)

    if errors:
        return render_template("results.html", errors=errors)

    # get results for current page
    start = (page - 1) * results_per_page
    end = min(start + results_per_page, len(results))
    page_results = results[start:end]

    # retrieve the first wrapper image and number of items of every group
    page_results = [Result(r.label, meta=_get_info_by_label(r.label)) for r in page_results]

    pagination = Pagination(
        page=page,
        total=len(results),
        search=False,
        record_name='resultaten',
        display_msg="<b>{start} - {end}</b> van <b>{total}</b> {record_name}",
        per_page=results_per_page,
        href='javascript:retrieveResults({0})',
        inner_window=1,
        outer_window=0,
    )

    return render_template("results.html",
                           results=page_results,
                           pagination=pagination,
                           navigation_links=create_navigation(pagination),
                           errors=None)


@results_page.route('/result/group', methods=['GET'])
def show_group():
    """
    Show the wrappers within a firework group
    """
    results_per_page = current_app.config['MAX_WRAPPERS_PER_RESULT']
    group_results = {}

    processed_get_request = process_get_request_group(request)
    errors = processed_get_request.errors
    page = processed_get_request.page
    group_id = processed_get_request.group_id

    if not errors:
        group_results = current_app.meta_data.get(group_id)['wrappers']

        if not group_results:
            errors.append(RESULTS_NOT_AVAILABLE)
        elif page <= 0 or len(group_results) <= (page - 1) * results_per_page:
            errors.append(RESULTS_NOT_AVAILABLE_FOR_PAGE)

    if errors:
        return render_template("group.html", errors=errors)

    # get results for current page
    start = (page - 1) * results_per_page
    end = min(start + results_per_page, len(group_results))

    page_results = [Result(label=group_id, meta={'image': group_results[key]['image'],
                                                 'article_name': group_results[key]['article_name'],
                                                 'item_id': key})
                    for key in list(group_results.keys())[start:end]]

    pagination = Pagination(
        page=page,
        total=len(group_results),
        search=False,
        record_name='artikelen in categorie',
        display_msg="<b>{start} - {end}</b> van <b>{total}</b> {record_name}",
        per_page=results_per_page,
        href='javascript:getGroupData(' + group_id + ',{0})',
        inner_window=1,
        outer_window=0,
    )

    return render_template("group.html",
                           group_id=group_id,
                           results=page_results,
                           pagination=pagination,
                           navigation_links=create_navigation(pagination),
                           errors=None)


@results_page.route('/result/item', methods=['GET'])
def show_item():
    """
    Show a single firework item
    """
    processed_get_request = process_get_request_item(request)
    errors = processed_get_request.errors
    group_id = processed_get_request.group_id
    item_id = processed_get_request.item_id

    if errors:
        return render_template("item.html", errors=errors)

    item = current_app.meta_data[group_id]["wrappers"][item_id]
    return render_template("item.html",
                           item=item,
                           meta_data_key_mapping=current_app.meta_data_key_mapping,
                           endangerment_mapping=current_app.endangerment_mapping,
                           errors=None)


@results_page.route('/images/<path:filename>')
def show_image(filename: str):
    if meta_data_dir := current_app.config.get("META_DATA_DIR", None):
        if pathlib.Path(filename).suffix in current_app.config["ALLOWED_EXTENSIONS"]:
            return send_from_directory(meta_data_dir, filename)
    return abort(404)
