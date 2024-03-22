from app.calculations.core import get_text_matches, get_results
from app.requests.messages import TOO_MANY_CHARACTERS, NO_MATCH_FOUND
from tests.utils import assert_texts_in_response


def test_request_run_model(client, app):
    """
    Request to run the model multiple times for different texts and text sizes
    """
    with client:
        # test if large query texts get rejected
        response = client.post("/results",
                               data=create_text_request_data_of_length(n_chars=app.config["MAX_CHARS_TEXT_FILTER"] + 1))
        assert_texts_in_response(response, [TOO_MANY_CHARACTERS])

        # test if app correctly returns that no match has been found
        response = client.post("/results",
                               data=create_text_request_data_of_length(n_chars=app.config["MAX_CHARS_TEXT_FILTER"] - 1))
        assert_texts_in_response(response, [NO_MATCH_FOUND])

        # test if app correctly returns a `results_id` in case of a text match
        response = client.post("/results", data={"text": "cobra", "file": ""})
        assert_texts_in_response(response, "results_id")
        response = client.post("/results", data={"text": "COBRA", "file": ""})
        assert_texts_in_response(response, "results_id")


def test_text_filter_matches(app):
    assert '125' in get_text_matches('cobra')
    assert len(get_text_matches('COBRA')) == 0
    assert len(get_text_matches('c')) == len(get_results(query_image=None, query_text='c')) == 6


def create_text_request_data_of_length(n_chars: int):
    return {"text": "a" * n_chars,
            "file": ""
            }
