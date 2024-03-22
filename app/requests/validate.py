import io
import re
from typing import Any, List, Mapping, NamedTuple, Optional, Tuple

from PIL import Image, JpegImagePlugin
from flask import current_app, request, Request
from unidecode import unidecode
from werkzeug.datastructures import FileStorage

from app.requests.messages import EMPTY_FILE, FILE_READ_FAILURE, INVALID_FILE_FORMAT, MISSING_PAGE_NUMBER, \
    MISSING_QUERY_DATA, MISSING_RESULTS_ID, WRONG_FORMAT_PAGE_NUMBER, TOO_MANY_CHARACTERS, MISSING_CATEGORY_ID, \
    WRONG_CATEGORY_ID, MISSING_ITEM_ID, WRONG_ITEM_ID

JpegImagePlugin._getmp = lambda x: None  # https://github.com/python-pillow/Pillow/issues/1138

FILTER_PATTERN = re.compile('[^a-z ]')


class ProcessedPostRequest(NamedTuple):
    text: str
    image_data: bytes
    errors: list


class ProcessedGetRequest(NamedTuple):
    page: int = None
    errors: list = None
    results_id: str = None
    group_id: str = None
    item_id: str = None


def clean_text(text: str) -> str:
    """
    Perform cleaning of input string. Use the same cleaning for the texts from the wrapper as the text on the images.
    Lowercase text, strip whitespace, remove accents from characters and remove non-alphabetic characters.
    """
    filtered = FILTER_PATTERN.sub('', unidecode(str(text).lower().strip()))
    # remove double white spaces
    return " ".join(filtered.split())


def _validate_image_data(image_data: Optional[bytes]) -> bool:
    try:
        image = Image.open(io.BytesIO(image_data))
        return image.format is not None and '.' + image.format.lower() in current_app.config['ALLOWED_EXTENSIONS']
    except IOError:
        return False


def _check_text_length(text: str) -> str:
    return len(text) <= current_app.config['MAX_CHARS_TEXT_FILTER']


def _process_uploaded_file(file: FileStorage) -> Tuple[Optional[bytes], List[str]]:
    errors = []
    image_data = None

    if file.filename == '':
        # If the user does not select a file, the browser submits
        # an empty file without a filename.
        errors.append(EMPTY_FILE)
        return image_data, errors

    try:
        # otherwise, try to parse the binary image data
        image_data = file.read()
        if not image_data:
            errors.append(EMPTY_FILE)
        elif not _validate_image_data(image_data):
            errors.append(INVALID_FILE_FORMAT)
    except Exception as e:
        errors.append(FILE_READ_FAILURE)

    return image_data, errors


def _process_form_data(form_data: Mapping[str, Any]) -> Tuple[Optional[str], Optional[List[str]]]:
    errors = []

    text = form_data.get('text', None)
    if text:
        if not _check_text_length(text):
            errors.append(TOO_MANY_CHARACTERS)
        else:
            text = clean_text(text)
    return text, errors


def _get_page_number_from_request(r: Request) -> Tuple[Optional[int], List[str]]:
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


def process_post_request(post_request: request) -> ProcessedPostRequest:
    if form := post_request.form:
        text, errors_form = _process_form_data(form)
    else:
        text, errors_form = None, []

    if post_request.files and (file := post_request.files.get('file', None)):
        image_data, errors_file = _process_uploaded_file(file)
    else:
        image_data, errors_file = None, []

    errors = errors_form + errors_file
    if not (text or image_data):
        errors.append(MISSING_QUERY_DATA)

    return ProcessedPostRequest(text=text,
                                image_data=image_data,
                                errors=errors)


def process_get_request_results(get_request: request) -> ProcessedGetRequest:
    errors = []
    results_id = None

    if 'id' in get_request.args:
        results_id = get_request.args.get('id')
    else:
        errors.append(MISSING_RESULTS_ID)

    page, e = _get_page_number_from_request(get_request)
    errors.extend(e)

    return ProcessedGetRequest(results_id=results_id,
                               page=page,
                               errors=errors)


def process_get_request_group(get_request: request):
    errors = []

    group_id = get_request.args.get('id', None)
    if not group_id or group_id == "":
        errors.append(MISSING_CATEGORY_ID)
    elif group_id not in current_app.meta_data.keys():
        errors.append(WRONG_CATEGORY_ID)

    page, e = _get_page_number_from_request(get_request)
    errors.extend(e)

    return ProcessedGetRequest(group_id=group_id,
                               page=page,
                               errors=errors)


def process_get_request_item(get_request: request):
    errors = []

    group_id = get_request.args.get('group_id', None)
    if not group_id or group_id == "":
        errors.append(MISSING_CATEGORY_ID)
    elif group_id not in current_app.meta_data.keys():
        errors.append(WRONG_CATEGORY_ID)

    item_id = get_request.args.get('item_id', None)
    if not item_id or item_id == "":
        errors.append(MISSING_ITEM_ID)
    elif item_id not in current_app.meta_data[group_id]["wrappers"].keys():
        errors.append(WRONG_ITEM_ID)

    return ProcessedGetRequest(group_id=group_id,
                               item_id=item_id,
                               errors=errors)
