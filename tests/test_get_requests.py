import json
import os

from app.requests.messages import (
    MISSING_PAGE_NUMBER,
    MISSING_RESULTS_ID,
    RESULTS_NOT_AVAILABLE,
    RESULTS_NOT_AVAILABLE_FOR_PAGE,
    WRONG_CATEGORY,
    WRONG_FORMAT_PAGE_NUMBER,
    WRONG_LABEL,
)
from config.render.meta_data_mapping import META_DATA_KEY_MAPPING
from tests.conftest import image_post_request_data
from tests.utils import SpyModel, assert_texts_in_response, assert_texts_not_in_response


def test_request_retrieve_results_empty_data(client):
    with client:
        response = client.get("/search/results")
        assert_texts_in_response(response, [MISSING_RESULTS_ID, MISSING_PAGE_NUMBER])


def test_request_retrieve_results_wrong_page_format(client):
    with client:
        response = client.get("/search/results?page=ThisIsNoNumber")
        assert_texts_in_response(response, [WRONG_FORMAT_PAGE_NUMBER])


def test_request_retrieve_results_not_in_cache(client):
    with client:
        response = client.get("/search/results?page=1&resultsId=NonExistent")
        assert_texts_in_response(response, [RESULTS_NOT_AVAILABLE])


def test_request_display_category(client, app):
    with client:
        category, page = '3040', '1'
        response = client.get(f"/categories/{category}?page={page}")
        assert_texts_in_response(response, ["Categorie", "3040"])


def test_request_display_incorrect_category(client, app):
    with client:
        category, page = 'abcde', '1'
        response = client.get(f"/categories/{category}?page={page}")
        assert_texts_in_response(response, [WRONG_CATEGORY])


def test_request_display_item(client, app):
    with client:
        # test if images are present
        category, label = '3040', '3040 vlinder xxl'
        response = client.get(f"/categories/{category}/articles/{label}")
        assert_texts_in_response(response, ["wrapper.png", "compleet%20exemplaar.png", "gedemonteerd.png"])
        # test if meta-data fields are hidden when values are not available
        assert_texts_not_in_response(response, ["Overige lading"])

        # test if meta-data is rendered correctly
        assert_texts_in_response(response, list(META_DATA_KEY_MAPPING.values()))
        assert_texts_in_response(
            response,
            ["3040 vlinder xxl", "Flash banger", "F3"],
        )

        # test if other compositions are shown correctly
        category, label = 'shell2', '3 inch kleuren shell'
        response = client.get(f"/categories/{category}/articles/{label}")
        assert_texts_in_response(response, ["F4"])


def test_request_retrieve_incorrect_item(client, app):
    with client:
        category, label = '3040', 'abcde'
        response = client.get(f"/categories/{category}/articles/{label}")
        assert_texts_in_response(response, [WRONG_LABEL])


def test_request_retrieve_results_not_available_for_page(client, app):
    with client:
        app.model = SpyModel()

        response = client.post("/search", data=image_post_request_data())
        results_id = json.loads(response.get_data(as_text=True))["results_id"]

        response = client.get(f"/search/results?resultsId={results_id}&page=0")
        assert_texts_in_response(response, [RESULTS_NOT_AVAILABLE_FOR_PAGE])

        response = client.get(f"/search/results?resultsId={results_id}&page=3")
        assert_texts_in_response(response, [RESULTS_NOT_AVAILABLE_FOR_PAGE])

        app.config['RESULTS_PER_PAGE'] = 6
        response = client.get(f"/search/results?resultsId={results_id}&page=2")
        assert_texts_in_response(response, [RESULTS_NOT_AVAILABLE_FOR_PAGE])


def test_request_retrieve_results(client, app):
    """Request to run the model, and after that request the (cached) results for multiple pages."""
    with client:
        spy_model = SpyModel()
        total_results = len(spy_model.categories())
        page_results = 3
        app.model = spy_model
        app.config['RESULTS_PER_PAGE'] = page_results
        assert spy_model.prediction_triggers == 0

        response = client.post("/search", data=image_post_request_data())
        assert_texts_in_response(response, ["results_id"])

        assert spy_model.prediction_triggers == 1

        results_id = json.loads(response.get_data(as_text=True))["results_id"]

        response = client.get(f"/search/results?resultsId={results_id}&page=1")

        # Check if the model is not triggered again and the cached results of page 1 are returned
        assert spy_model.prediction_triggers == 1
        assert response.status_code == 200
        assert_texts_in_response(
            response,
            [f"<b>1 - {page_results}</b> van <b>{total_results}</b> resultaten"],
        )
        # Check if the model is not triggered again and the cached results of page 2 are returned
        response = client.get(f"/search/results?resultsId={results_id}&page=2")
        assert spy_model.prediction_triggers == 1
        assert response.status_code == 200
        assert_texts_in_response(
            response,
            [f"<b>{page_results + 1} - {total_results}</b> van <b>{total_results}</b> resultaten"],
        )
        # Check if results not available for higher page numbers
        response = client.get(f"/search/results?resultsId={results_id}&page=3")
        assert_texts_in_response(
            response,
            [RESULTS_NOT_AVAILABLE_FOR_PAGE],
        )


def test_show_image(client, app):
    test_filename = "3040/3040 vlinder xxl/wrapper.png"
    test_image_path = os.path.join(app.config["REFERENCE_DATA_DIR"], test_filename)
    with open(test_image_path, "rb") as f:
        file_bytes = f.read()

    response = client.get(f"/images/{test_filename}")
    assert response.data == file_bytes
    assert response.status_code == 200


def test_get_request_no_result_id_used(client):
    with client:
        response = client.get("/search/results?")
        assert_texts_in_response(response, [MISSING_RESULTS_ID, MISSING_PAGE_NUMBER])
