import hashlib
from random import Random
from typing import Mapping, Set, Sequence

from PIL import Image

from app.calculations.models.base import ClassificationModel


class DummyModel(ClassificationModel):
    """
    A dummy image classifier that generates nonsensical output, but can be used
    for functional testing or demonstrative purposes.
    """

    def __init__(self, labels: Sequence[str] = None):
        """
        Instantiate the dummy model.

        :param labels: A list of textual labels for which dummy classification
            confidence scores will be generated.
        """
        self._labels = set(labels)

    def predict(self, image: Image) -> Mapping[str, float]:
        seed = hashlib.sha256(image.tobytes()).hexdigest()
        r = Random(seed)
        predictions = {label: r.random() for label in self.labels}
        return predictions

    @property
    def labels(self) -> Set[str]:
        return self._labels
