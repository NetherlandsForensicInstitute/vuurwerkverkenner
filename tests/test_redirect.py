from tests.utils import assert_texts_in_response


def test_404_redirect_to_index(client):
    # Test if page not found exceptions get redirected
    assert_get_redirect_to_index(client, "ManManManDezeBestaatTochNiet")
    assert_get_redirect_to_index(client, "index/bla")
    assert_get_redirect_to_index(client, "about/onzin/NogMeerOnzin")
    assert_get_redirect_to_index(client, "results/1/2/3/4")


def test_405_redirect_to_index_(client):
    # Test if method not allowed exceptions get redirected
    with client:
        path = "/help"

        # Sanity check that the help page exists (but with a GET request, no POST)
        response = client.get(path, follow_redirects=False)
        assert response.request.path == path

        # Check that a POST request to the help page gets redirected
        response = client.post(path, follow_redirects=True, data={})
        assert_redirect_to_index(response)

        # Try to send a PUT request to '/results' (which only accepts GET and POST request)
        response = client.put("/results", follow_redirects=True, data={})
        assert_redirect_to_index(response)


def test_non_http_exception_redirects(client):
    # Test that application exceptions get redirected
    assert_get_redirect_to_index(client, "/generate_non_http_exception")


def test_http_exceptions(client):
    # Test that some common HTTP status codes (other than 404 and 405) are returned
    for status in [400, 401, 403, 408, 413, 500, 501]:
        response = client.get(f"/generate_http_exception/{status}")
        assert response.status_code == status


def assert_get_redirect_to_index(client, path):
    response = client.get(path, follow_redirects=True)
    assert_redirect_to_index(response)


def assert_redirect_to_index(response):
    assert response.request.path == '/index'
    assert response.status_code == 200
    assert len(response.history) == 1

    assert_texts_in_response(response, ["Vuurwerkverkenner", "Upload snipperfoto", "Voer tekst in", "Verken vuurwerk"])
