from app.requests.validate import _check_text_length as check_text_length


def test_too_many_characters(app):
    ok_text = "a" * (app.config["MAX_CHARS_TEXT_FILTER"] - 1)
    assert check_text_length(ok_text)

    too_long_text = "a" * (app.config["MAX_CHARS_TEXT_FILTER"] + 1)
    assert not check_text_length(too_long_text)
