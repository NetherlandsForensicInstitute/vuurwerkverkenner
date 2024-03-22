from abc import abstractmethod, ABC
from typing import Mapping, Set

import numpy as np
from PIL import Image


class ClassificationModel(ABC):
    """
    Abstract base class that specifies the interface all classification models must adhere to.
    """

    @abstractmethod
    def predict(self, image: Image) -> Mapping[str, float]:
        """
        Make predictions for a single image instance

        :param image: The instance to make predictions for
        :returns: The model prediction which is a mapping between labels and scores
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def labels(self) -> Set[str]:
        raise NotImplementedError


class EmbeddingModel(ABC):
    """
    Abstract base class that specifies the interface all embedding models must adhere to.
    """

    @abstractmethod
    def predict(self, image: Image) -> np.ndarray:
        """
        Compute an embedding vector for a single image instance

        :param image: The instance to create the embedding for
        :returns: A numpy array containing the embedding vector
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def embedding_size(self) -> int:
        raise NotImplementedError
