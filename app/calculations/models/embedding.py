from typing import Optional, Tuple

import numpy as np
import tensorflow as tf
from PIL import Image
from keras import layers
from vit_keras import vit

from app.calculations.models.base import EmbeddingModel
from app.calculations.models.utils import min_max_normalize, convert_PIL_image_to_numpy


class EmbeddingViTModel(EmbeddingModel):
    """
    The class for an embedding model that is built on top of the Vision Transformer
    with the option to load the model with pretrained weights.
    """

    def __init__(self,
                 input_size: Tuple[int, int],
                 embedding_size: int,
                 weights_file: Optional[str] = None,
                 backbone: str = "vit_b32"):
        """
        :param input_size: the size of the model's input layer
        :param embedding_size: the size of the embedding layer (= model output)
        :param weights_file: (optionally) the file path corresponding to the pretrained weights file
            the model should be instantiated with
        :param backbone: which backbone to use (either 'vit_b16', 'vit_b32' or 'vit_l32')
        """
        self._input_size = input_size
        self._backbone = self._create_backbone(backbone)
        self._embedding_size = embedding_size
        self._model = self._build_model()
        if weights_file:
            self._load_weights(weights_file)

    def predict(self, image: Image) -> np.ndarray:
        # resize the PIL image to the right input size and convert to numpy array:
        image = convert_PIL_image_to_numpy(image, resize=self._input_size)
        # map the signal intensities to the [-1, 1] range by applying min-max normalization
        image = min_max_normalize(image)
        # compute and return the embedding for the normalized map
        embedding = self._model.predict(image.reshape(1, *image.shape), verbose=0).reshape(self.embedding_size)
        return embedding

    @property
    def embedding_size(self) -> int:
        return self._embedding_size

    def _create_backbone(self, backbone: str) -> tf.keras.Sequential:
        if backbone == "vit_b16":
            return vit.vit_b16(
                image_size=self._input_size,
                activation='sigmoid',
                pretrained=False,
                include_top=False,
                pretrained_top=False,
            )
        elif backbone == "vit_b32":
            return vit.vit_b32(
                image_size=self._input_size,
                activation='sigmoid',
                pretrained=False,
                include_top=False,
                pretrained_top=False,
            )
        elif backbone == "vit_l32":
            return vit.vit_l32(
                image_size=self._input_size,
                activation='sigmoid',
                pretrained=False,
                include_top=False,
                pretrained_top=False,
            )
        else:
            raise NotImplementedError

    def _build_model(self) -> tf.keras.Sequential:
        return tf.keras.Sequential([
            self._backbone,
            layers.Dense(self.embedding_size, activation=None),
            layers.Lambda(lambda x: tf.math.l2_normalize(x, axis=1), name='embedding')
        ])

    def _load_weights(self, weights_file: str):
        self._model.load_weights(weights_file)
