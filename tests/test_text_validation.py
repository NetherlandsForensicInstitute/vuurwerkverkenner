from app.requests.validate import _check_text_length as check_text_length
from tests.test_text_filter import create_text_request_data_of_length


def test_too_many_characters(app):
    ok_text = create_text_request_data_of_length(n_chars=app.config["MAX_CHARS_TEXT_FILTER"] - 1)["text"]
    assert check_text_length(ok_text)

    too_long_text = create_text_request_data_of_length(n_chars=app.config["MAX_CHARS_TEXT_FILTER"] + 1)["text"]
    assert not check_text_length(too_long_text)
