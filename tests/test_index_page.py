import io

from app.requests.messages import EMPTY_FILE, INVALID_FILE_FORMAT, MISSING_QUERY_DATA, NO_MATCH_FOUND
from tests.conftest import TEST_RESOURCES_DIR
from tests.utils import assert_help_button_in_response, assert_response_on_path_without_redirects, \
    assert_texts_in_response


def test_index_page(client):
    assert_index_page_on('/index', client)


def test_security_file(client):
    with client:
        response = client.get("/.well-known/security.txt")
        assert_texts_in_response(response, "Contact: https://www.forensischinstituut.nl/")


def test_default_page_is_index_page(client):
    assert_index_page_on('/', client)


def test_post_request_empty_data(client):
    with client:
        response = client.post("/results", data=None)
        assert_texts_in_response(response, MISSING_QUERY_DATA)


def test_post_request_no_file(client):
    with client:
        response = client.post("/results", data=create_request_data(text="", file=None, filename='Geen'))
        assert_texts_in_response(response, [MISSING_QUERY_DATA, EMPTY_FILE])


def test_post_request_empty_file_name(client):
    with client:
        response = client.post("/results", data=create_request_data(text="", file=io.BytesIO(b"abcdef"), filename=''))
        assert_texts_in_response(response, MISSING_QUERY_DATA)


def test_post_request_wrong_file_format(client):
    with client:
        response = client.post("/results",
                               data=create_request_data(text="", file=io.BytesIO(b"abcdef"), filename='test.png'))
        assert_texts_in_response(response, INVALID_FILE_FORMAT)


def test_post_request_trigger_model(client):
    with open(f'{TEST_RESOURCES_DIR}/snippet_cobra.png', 'rb') as f:
        file_bytes = f.read()

    with client:
        response = client.post("/results", data=create_request_data(
            text="cObRa",
            file=io.BytesIO(file_bytes),
            filename='test.jpg'))
        assert_texts_in_response(response, ["results_id"])


def test_post_request_no_results(client):
    with open(f'{TEST_RESOURCES_DIR}/snippet_cobra.png', 'rb') as f:
        file_bytes = f.read()

    with client:
        response = client.post("/results", data=create_request_data(
            text="cObRa die zit er niet in!!!",
            file=io.BytesIO(file_bytes),
            filename='test.jpg'))
        assert_texts_in_response(response, ["errors"])
        assert_texts_in_response(response, [NO_MATCH_FOUND])


def create_request_data(text: str = "", file: io.BytesIO = None, filename: str = "", page: int = 1):
    return {"text": text, "file": (file, filename), "page": page}


def assert_index_page_on(path, client):
    response = assert_response_on_path_without_redirects(path, client)
    assert_texts_in_response(response, [
        "Vuurwerkverkenner", "Upload snipperfoto", "Voer tekst in", "Verken vuurwerk"
    ])
    assert_help_button_in_response(response)
