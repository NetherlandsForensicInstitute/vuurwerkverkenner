import numpy as np

from app.calculations.models import ClassificationModel


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

    response_text = response.get_data(as_text=True)
    assert all(str(expected_text) in response_text for expected_text in expected_texts)


def assert_texts_not_in_response(response, texts):
    if isinstance(texts, str):
        texts = [texts]

    response_text = response.get_data(as_text=True)
    assert all(str(expected_text) not in response_text for expected_text in texts)


class SpyModel(ClassificationModel):
    """Model which keeps track of the number of calls to the predict method."""

    prediction_triggers = 0
    predictions = {
        ("3040", "3040 vlinder xxl"): 1.0,
        ("ghost1", "9705 zylinderrakete ghost"): 1.0,
        ("match_cracker2", "12 match cracker"): 1.0,
        ("shell1", "3 inch report shell"): 1.0,
        ("shell1", "6 inch report shell"): 1.0,
        ("shell2", "3 inch kleuren shell"): 1.0,
    }

    def predict(self, instance: np.ndarray) -> dict[tuple[str, str], float]:
        self.prediction_triggers += 1
        return self.predictions

    def categories(self) -> set[str]:
        return set(item[0] for item in self.predictions)

    def load(self):
        pass
