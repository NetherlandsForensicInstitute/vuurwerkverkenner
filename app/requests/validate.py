import io
import re
from typing import NamedTuple

from flask import Request, current_app
from PIL import Image, JpegImagePlugin
from unidecode import unidecode
from werkzeug.datastructures import FileStorage

from app.requests.messages import (
    EMPTY_FILE,
    FILE_READ_FAILURE,
    INVALID_FILE_FORMAT,
    MISSING_CATEGORY,
    MISSING_LABEL,
    MISSING_PAGE_NUMBER,
    MISSING_RESULTS_ID,
    TOO_MANY_CHARACTERS,
    WRONG_CATEGORY,
    WRONG_FORMAT_PAGE_NUMBER,
    WRONG_LABEL,
)

JpegImagePlugin._getmp = lambda x: None  # https://github.com/python-pillow/Pillow/issues/1138

FILTER_PATTERN = re.compile('[^a-z ]')
FILTER_PATTERN_INCLUDING_DIGITS = re.compile('[^a-z0-9 ]')


class ProcessedPostRequest(NamedTuple):
    image_data: bytes | None
    query_text: str | None
    text_filter: bool
    include_digits: bool
    errors: list


class ProcessedGetRequest(NamedTuple):
    page: int | None = None
    errors: list | None = None
    results_id: str | None = None
    category: str | None = None
    label: str | None = None


def clean_text(text: str, include_digits: bool = True) -> str:
    """
    Perform cleaning of input string. Use the same cleaning for the texts from the wrapper as the text on the images.
    Lowercase text, strip whitespace, remove accents from characters and remove non-alphabetic characters.
    """
    pattern = FILTER_PATTERN_INCLUDING_DIGITS if include_digits else FILTER_PATTERN
    filtered = pattern.sub('', unidecode(str(text).lower().strip()))

    # remove double white spaces
    return " ".join(filtered.split())


def _validate_image_data(image_data: bytes | None) -> bool:
    """Check if the image data is valid."""
    try:
        image = Image.open(io.BytesIO(image_data))
        return image.format is not None and '.' + image.format.lower() in current_app.config['ALLOWED_EXTENSIONS']
    except OSError:
        return False


def _check_text_length(text: str) -> str:
    """Check if the text is shorter than the maximum allowed length."""
    return len(text) <= current_app.config['MAX_CHARS_TEXT_FILTER']


def _process_uploaded_file(file: FileStorage) -> tuple[bytes | None, list[str]]:
    """Process the uploaded file from the form supplied by the user."""
    errors = []
    image_data = None

    try:
        # otherwise, try to parse the binary image data
        image_data = file.read()
        if not image_data:
            errors.append(EMPTY_FILE)
        elif not _validate_image_data(image_data):
            errors.append(INVALID_FILE_FORMAT)
    except Exception:
        errors.append(FILE_READ_FAILURE)

    return image_data, errors


def _get_page_number_from_request(r: Request) -> tuple[int | None, list[str]]:
    """Get page number from the page variable in the request, used for pagination."""
    page = None
    errors = []

    if 'page' in r.args:
        try:
            page = int(r.args.get('page'))
        except ValueError:
            errors.append(WRONG_FORMAT_PAGE_NUMBER)
    else:
        errors.append(MISSING_PAGE_NUMBER)

    return page, errors


def process_post_request(post_request: Request) -> ProcessedPostRequest:
    """Process POST-request."""
    errors = []
    image_data = None

    if post_request.files:
        file = post_request.files.get('file')

        if file is not None and file.filename == '':
            # If the user does not select a file, the browser submits
            # an empty file without a filename.
            errors.append(EMPTY_FILE)
        if file:
            image_data, errors_file = _process_uploaded_file(file)
            errors.extend(errors_file)
    return ProcessedPostRequest(
        image_data=image_data,
        query_text=post_request.form.get('query_text'),
        text_filter=post_request.form.get('text_filter', '').lower() == 'true',
        include_digits=post_request.form.get('include_digits', '').lower() == 'true',
        errors=errors,
    )


def process_query_text(query_text, include_digits) -> tuple[str | None, list[str]]:
    errors = []
    if query_text:
        if not _check_text_length(query_text):
            errors.append(TOO_MANY_CHARACTERS)
        else:
            query_text = clean_text(query_text, include_digits)
    return query_text, errors


def process_get_request_results_page(get_request: Request) -> ProcessedGetRequest:
    """Process GET-request for results based on the randomly generated results_id."""
    errors = []

    if not (results_id := get_request.args.get('resultsId')):
        errors.append(MISSING_RESULTS_ID)

    page, errs = _get_page_number_from_request(get_request)
    errors.extend(errs)

    return ProcessedGetRequest(results_id=results_id, page=page, errors=errors)


def process_get_request_category_page(get_request: Request, category: str | None):
    """Process GET-request for a specific firework category based on the category."""
    errors = []

    if not category:
        errors.append(MISSING_CATEGORY)
    elif category not in current_app.meta_data:
        errors.append(WRONG_CATEGORY)
    results_id = get_request.args.get('resultsId')
    page, errs = _get_page_number_from_request(get_request)
    errors.extend(errs)

    return ProcessedGetRequest(category=category, page=page, results_id=results_id, errors=errors)


def process_get_request_article_page(category: str | None, label: str | None) -> ProcessedGetRequest:
    """Process GET-request for a specific firework article based on the category and label."""
    errors = []
    if not label:
        errors.append(MISSING_LABEL)

    if not category:
        errors.append(MISSING_CATEGORY)
    elif category not in current_app.meta_data:
        errors.append(WRONG_CATEGORY)
    elif label not in current_app.meta_data[category]:
        errors.append(WRONG_LABEL)

    return ProcessedGetRequest(category=category, label=label, errors=errors)
