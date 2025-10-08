from PIL import Image

from app.requests.validate import _validate_image_data as validate_image_data
from tests.conftest import TEST_RESOURCES_DIR, large_image_request_data


# Sanity check (even though we don't use the file name)
def test_format_from_content_not_from_file_name(app):
    image = Image.open(f'{TEST_RESOURCES_DIR}/not_a_png.png')
    assert image.format == 'JPEG'


def test_jpeg(app):
    with open(f'{TEST_RESOURCES_DIR}/snippet_shark_3.jpg', 'rb') as f:
        assert validate_image_data(f.read()) is True


def test_gif(app):
    with open(f'{TEST_RESOURCES_DIR}/snippet_gigant_maroon.gif', 'rb') as f:
        assert validate_image_data(f.read()) is True


def test_png(app):
    with open(f'{TEST_RESOURCES_DIR}/snippet_cobra.png', 'rb') as f:
        assert validate_image_data(f.read()) is True


def test_txt(app):
    with open(f'{TEST_RESOURCES_DIR}/test.txt', 'rb') as f:
        assert validate_image_data(f.read()) is False


def test_non_existent(app):
    assert validate_image_data(None) is False


# test large files
def test_request_run_model(client, app):
    """Request to run the model multiple times for different image sizes."""
    with client:
        response = client.post(
            "/search", data=large_image_request_data(file_size=app.config["MAX_CONTENT_LENGTH"] + 1000)
        )
        assert response.status_code == 413  # REQUEST ENTITY TOO LARGE
        response = client.post(
            "/search", data=large_image_request_data(file_size=app.config["MAX_CONTENT_LENGTH"] - 1000)
        )
        assert response.status_code == 200  # OK
