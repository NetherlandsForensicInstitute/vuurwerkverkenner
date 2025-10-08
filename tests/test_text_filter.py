from app.requests.messages import NO_MATCH_FOUND, TOO_MANY_CHARACTERS
from tests.conftest import image_post_request_data
from tests.utils import assert_texts_in_response


def test_text_filter(client, app, results_id):
    """Request to search multiple times for different texts and text sizes."""
    with client:
        # test if large query texts get rejected
        response = client.post(
            "/search",
            data=image_post_request_data(
                query_text="a" * (app.config["MAX_CHARS_TEXT_FILTER"] + 1), text_filter="true", include_digits="false"
            ),
        )
        assert_texts_in_response(response, [TOO_MANY_CHARACTERS])

        # test if app correctly returns that no match has been found
        response = client.post(
            "/search",
            data=image_post_request_data(
                query_text="a" * (app.config["MAX_CHARS_TEXT_FILTER"] - 1), text_filter="true", include_digits="false"
            ),
        )
        assert_texts_in_response(response, [NO_MATCH_FOUND])
