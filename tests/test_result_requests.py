import io
import json
import os
from typing import Hashable, Mapping, Set, Union

from app.calculations.models import ClassificationModel
from app.requests.messages import MISSING_PAGE_NUMBER, MISSING_RESULTS_ID, RESULTS_NOT_AVAILABLE, \
    RESULTS_NOT_AVAILABLE_FOR_PAGE, WRONG_FORMAT_PAGE_NUMBER, WRONG_CATEGORY_ID, WRONG_ITEM_ID
from tests.conftest import TEST_RESOURCES_DIR
from tests.utils import assert_texts_in_response, assert_texts_not_in_response


def test_request_display_group(client, app):
    with client:
        group_id, page = '6', '1'
        response = client.get("/result/group?id=" + group_id + "&page=" + page)
        assert_texts_in_response(response, ["Categorie", "Thunderking"])

        # test if placeholder works when article_name is empty
        group_id, page = '125', '1'
        response = client.get("/result/group?id=" + group_id + "&page=" + page)
        assert_texts_in_response(response, ["Bekijk artikel"])


def test_request_display_incorrect_group(client, app):
    with client:
        group_id, page = 'abcde', '1'
        response = client.get("/result/group?id=" + group_id + "&page=" + page)
        assert_texts_in_response(response, [WRONG_CATEGORY_ID])


def test_request_display_item(client, app):
    with client:
        # test if images are present
        group_id, item_id = '6', '0'
        response = client.get("/result/item?group_id=" + group_id + "&item_id=" + item_id)
        assert_texts_in_response(response,
                                 ["wrapper.jpg", "compleet%20exemplaar.jpg", "gedemonteerd.jpg", "schematisch.jpg"])

        # test if meta-data is rendered correctly
        assert_texts_in_response(response, list(app.meta_data_key_mapping.values()))
        assert_texts_in_response(response, ["Thunderking", "Vuurpijl met knallading", "F4", "6.6",
                                            "kaliumperchloraat, zwavel, magnalium en mogelijk aluminium"])

        # test if other compositions are shown correctly
        group_id, item_id = '88', '2'
        response = client.get("/result/item?group_id=" + group_id + "&item_id=" + item_id)
        assert_texts_in_response(response, ["zwavel, kaliumnitraat en visueel koolstof"])

        # test if meta-data fields are hidden when values are not available
        group_id, item_id = '122', '0'
        response = client.get("/result/item?group_id=" + group_id + "&item_id=" + item_id)
        assert_texts_not_in_response(response,
                                     ["Overige lading", "Massa (g)", app.meta_data_key_mapping['tube_diameter']])


def test_request_retrieve_incorrect_item(client, app):
    with client:
        group_id, item_id = '6', 'abcde'
        response = client.get("/result/item?group_id=" + group_id + "&item_id=" + item_id)
        assert_texts_in_response(response, [WRONG_ITEM_ID])


def test_request_run_model(client, app):
    """
    Request to run the model multiple times for an image, check if the model is triggered every time
    """
    with client:
        spy_model = SpyModel()
        app.model = spy_model
        assert spy_model.prediction_triggers == 0

        response = client.post("/results", data=create_image_request_data())
        assert_texts_in_response(response, ["results_id"])
        assert spy_model.prediction_triggers == 1

        response = client.post("/results", data=create_image_request_data())
        assert_texts_in_response(response, ["results_id"])
        assert spy_model.prediction_triggers == 2


def test_request_retrieve_results(client, app):
    """
    Request to run the model, and after that request the (cached) results for multiple pages
    """
    with client:
        spy_model = SpyModel()
        total_results = len(spy_model.labels())
        page_results = 5
        app.model = spy_model
        app.config['MAX_WRAPPERS_PER_RESULT'] = page_results
        assert spy_model.prediction_triggers == 0

        response = client.post("/results", data=create_image_request_data())
        assert_texts_in_response(response, ["results_id"])

        assert spy_model.prediction_triggers == 1

        results_id = json.loads(response.get_data(as_text=True))["results_id"]

        response = client.get("/results?id=" + results_id + "&page=1")

        # Check if the model is not triggered again and the cached results of page 1 are returned
        assert spy_model.prediction_triggers == 1
        assert_texts_in_response(response, [
            f"<b>1 - {page_results}</b> van <b>{total_results}</b> resultaten",
            "javascript:retrieveResults(2)"
        ])

        response = client.get("/results?id=" + results_id + "&page=2")

        # Check if the model is not triggered again and the cached results of page 2 are returned
        assert spy_model.prediction_triggers == 1
        assert_texts_in_response(response, [
            f"<b>{page_results + 1} - {min(page_results * 2, total_results)}</b> van <b>{total_results}</b> resultaten",
            "javascript:retrieveResults(1)"
        ])


def test_request_retrieve_results_empty_data(client):
    with client:
        response = client.get("/results")
        assert_texts_in_response(response, [MISSING_RESULTS_ID, MISSING_PAGE_NUMBER])


def test_request_retrieve_results_wrong_page_format(client):
    with client:
        response = client.get("/results?page=ThisIsNoNumber")
        assert_texts_in_response(response, [WRONG_FORMAT_PAGE_NUMBER])


def test_request_retrieve_results_not_in_cache(client):
    with client:
        response = client.get("/results?page=1&id=NonExistent")
        assert_texts_in_response(response, [RESULTS_NOT_AVAILABLE])


def test_request_retrieve_results_not_available_for_page(client, app):
    with client:
        app.model = SpyModel()

        response = client.post("/results", data=create_image_request_data())
        results_id = json.loads(response.get_data(as_text=True))["results_id"]

        response = client.get("/results?id=" + results_id + "&page=0")
        assert_texts_in_response(response, [RESULTS_NOT_AVAILABLE_FOR_PAGE])

        response = client.get("/results?id=" + results_id + "&page=3")
        assert_texts_in_response(response, [RESULTS_NOT_AVAILABLE_FOR_PAGE])

        app.config['RESULTS_PER_PAGE'] = 6
        response = client.get("/results?id=" + results_id + "&page=2")
        assert_texts_in_response(response, [RESULTS_NOT_AVAILABLE_FOR_PAGE])


def test_show_image(client, app):
    test_filename = "fireworks_170/wrappers/0/wrapper.jpg"
    test_image_path = os.path.join(app.config["META_DATA_DIR"], test_filename)
    with open(test_image_path, "rb") as f:
        file_bytes = f.read()

    response = client.get(f"/images/{test_filename}")
    assert response.data == file_bytes
    assert response.status_code == 200


def create_image_request_data():
    with open(f'{TEST_RESOURCES_DIR}/snippet_cobra.png', 'rb') as f:
        file_bytes = f.read()
    return {"text": "", "file": (io.BytesIO(file_bytes), "test.jpg")}


def create_large_image_request_data(file_size: int):
    return {"text": "",
            "file": (io.BytesIO(bytearray(os.urandom(file_size))), "test.jpg")
            }


class SpyModel(ClassificationModel):
    """
    Model which keeps track of the number of calls to the predict method
    """
    prediction_triggers = 0
    predictions = {"122": 8, "125": 6, "168": 4, "170": 9, "6": 7,
                   "88": 5}

    def predict(self, image: Union[bytes, Hashable]) -> Mapping[str, float]:
        self.prediction_triggers += 1
        return self.predictions

    def labels(self) -> Set[str]:
        return set(self.predictions.keys())
