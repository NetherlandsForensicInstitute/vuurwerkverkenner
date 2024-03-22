from app.requests.validate import clean_text


def test_clean_text():
    assert clean_text("") == ""
    assert clean_text("aa") == "aa"
    assert clean_text("BB") == "bb"
    assert clean_text(" c C ") == "c c"
    assert clean_text("1d2d3") == "dd"
    assert clean_text(" è é ") == "e e"
    assert clean_text(" a b  c   d      e ") == "a b c d e"
