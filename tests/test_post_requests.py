import io
import json

from app.requests.messages import EMPTY_FILE, INVALID_FILE_FORMAT, NO_MATCH_FOUND
from tests.conftest import TEST_RESOURCES_DIR, image_post_request_data, post_request_data
from tests.utils import SpyModel, assert_texts_in_response


def test_post_request_no_file(client):
    with client:
        response = client.post("/search", data=post_request_data(file=None, filename='test.png'))
        assert_texts_in_response(response, [EMPTY_FILE])


def test_post_request_empty_file_name(client):
    with client:
        response = client.post("/search", data=post_request_data(file=io.BytesIO(b"abcdef"), filename=''))
        assert_texts_in_response(response, [EMPTY_FILE])


def test_post_request_wrong_file_format(client):
    with client:
        response = client.post(
            "/search", data=post_request_data(file=io.BytesIO(b"abcdef"), filename='test.wrong_format')
        )
        assert_texts_in_response(response, [INVALID_FILE_FORMAT])


def test_post_request_trigger_model(client):
    with open(f'{TEST_RESOURCES_DIR}/snippet_cobra.png', 'rb') as f:
        file_bytes = f.read()

    with client:
        response = client.post("/search", data=post_request_data(file=io.BytesIO(file_bytes), filename='test.jpg'))
        assert_texts_in_response(response, ["results_id"])


def test_post_request_empty(client):
    with client:
        response = client.post("/search", data=None)
        assert 'results_id' in response.json


def test_request_run_model(client, app):
    """Request to run the model multiple times for an image, check if the model is triggered every time."""
    with client:
        spy_model = SpyModel()
        app.model = spy_model
        assert spy_model.prediction_triggers == 0

        response = client.post("/search", data=image_post_request_data())
        assert_texts_in_response(response, ["results_id"])
        assert spy_model.prediction_triggers == 1

        response = client.post("/search", data=image_post_request_data())
        assert_texts_in_response(response, ["results_id"])
        assert spy_model.prediction_triggers == 2


def test_post_request_no_match_found(client, results_id):
    with client:
        response = client.post(
            "/search", data=image_post_request_data(query_text="cObRa die zit er niet in!!!", text_filter='true')
        )
    assert_texts_in_response(response, [NO_MATCH_FOUND])


def test_post_request_include_digits(client):
    with client:
        response = client.post(
            "/search",
            data=image_post_request_data(
                query_text="123456789 match cracker", text_filter="true", include_digits="false"
            ),
        )
        results_id = json.loads(response.get_data(as_text=True))["results_id"]
        assert results_id

        response = client.post(
            "/search",
            data=image_post_request_data(
                query_text="123456789 match cracker", text_filter="true", include_digits="true"
            ),
        )
        assert_texts_in_response(response, [NO_MATCH_FOUND])


def test_post_request_script_injection_text(client, results_id):
    with client:
        response = client.post(
            "/search",
            data=image_post_request_data(
                query_text="<script>alert('xss')</script>", text_filter="true", include_digits="false"
            ),
        )
        assert_texts_in_response(response, [NO_MATCH_FOUND])
