import os
from abc import ABC, abstractmethod
from collections.abc import Mapping

import numpy as np
import torch


class ClassificationModel(ABC):
    """
    Abstract base class that specifies the interface all classification models must adhere to.
    """

    @abstractmethod
    def predict(self, image: np.ndarray) -> Mapping[str, float]:
        """
        Make predictions for a single image instance.

        :param image: The instance to make predictions for as a numpy array
        :returns: The model prediction which is a mapping between labels and scores
        """
        raise NotImplementedError


class EmbeddingModel(ABC, torch.nn.Module):
    @abstractmethod
    def forward(self, images: torch.Tensor) -> torch.Tensor:
        """Implement the forward pass of the model."""
        raise NotImplementedError

    def load(self, path: str, device: str = 'cpu'):
        """Load the model weights from the given path."""
        if not os.path.exists(path):
            raise ValueError(f"Path {path} does not exist")

        self.load_state_dict(torch.load(path, map_location=torch.device(device), weights_only=True))
        print(f"Model weights successfully loaded from {path}")

    @property
    @abstractmethod
    def input_size(self) -> int:
        raise NotImplementedError

    @property
    @abstractmethod
    def embedding_size(self) -> int:
        raise NotImplementedError
