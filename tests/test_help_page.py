from tests.utils import assert_response_on_path_without_redirects, assert_texts_in_response


def test_help_page(client):
    response = assert_response_on_path_without_redirects('/help', client)
    assert_texts_in_response(
        response, ("Veelgestelde vragen", "Waar kan ik de Vuurwerkverkenner voor gebruiken?", "GitHub", "commit hash")
    )
