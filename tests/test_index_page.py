from tests.utils import (
    assert_help_button_in_response,
    assert_response_on_path_without_redirects,
    assert_texts_in_response,
)


def test_index_page(client):
    assert_index_page_on('/index', client)


def test_security_file(client):
    with client:
        response = client.get("/.well-known/security.txt")
        assert_texts_in_response(response, "Contact: https://www.forensischinstituut.nl/")


def test_default_page_is_index_page(client):
    assert_index_page_on('/', client)


def assert_index_page_on(path, client):
    response = assert_response_on_path_without_redirects(path, client)
    assert_texts_in_response(response, ["Vuurwerkverkenner", "Upload snipperfoto", "Voer tekst in", "Verken vuurwerk"])
    assert_help_button_in_response(response)
