from PIL import Image
import numpy as np

from app.calculations.models import DummyModel
from app.calculations.models.utils import segment_snippets


def test_prediction_dummy_model(dummy_model: DummyModel, test_image: Image):
    predictions = dummy_model.predict(np.asarray(test_image, dtype=np.uint8))
    labels = dummy_model.labels
    assert len(predictions) == len(labels)
    assert all(label in predictions.keys() for label in labels)


def test_loaded_model(app, test_image: Image):
    # test if the dummy model has been loaded in the app
    model = app.model
    labels = model.labels if isinstance(model, DummyModel) else None
    if labels:
        # test if the dummy model can make predictions
        predictions = model.predict(np.asarray(test_image, dtype=np.uint8))
        assert len(predictions) == len(labels)
        assert all(label in predictions.keys() for label in labels)


def test_segment_snippets(snippet_overview: Image):
    snippets = list(segment_snippets(snippet_overview))
    assert len(snippets) == 18
