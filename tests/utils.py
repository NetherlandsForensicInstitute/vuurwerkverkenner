def assert_response_on_path_without_redirects(path, client):
    response = client.get(path)

    assert response.request.path == path
    assert response.status_code == 200
    assert len(response.history) == 0

    return response


def assert_help_button_in_response(response):
    assert_texts_in_response(response, ['onclick="loadHelp()"'])


def assert_texts_in_response(response, expected_texts):
    if isinstance(expected_texts, str):
        expected_texts = [expected_texts]

    for expected_text in expected_texts:
        assert expected_text in response.get_data(as_text=True)


def assert_texts_not_in_response(response, texts):
    if isinstance(texts, str):
        texts = [texts]

    for text in texts:
        assert text not in response.get_data(as_text=True)
