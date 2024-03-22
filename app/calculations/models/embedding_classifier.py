from typing import Callable, Dict, Mapping, Sequence

import numpy as np
from PIL import Image
from flask import current_app
from numpy import mean, median
from scipy.spatial.distance import cdist

from app.calculations.models.base import ClassificationModel, EmbeddingModel
from app.calculations.models.utils import segment_snippets

AGGREGATORS: Dict[str, Callable[[Sequence[float]], float]] = {
    'min': min,
    'max': max,
    'mean': mean,
    'median': median
}


class EmbeddingClassifierModel(ClassificationModel):
    """
    Wrapper model that creates a classification model out of an embedding
    model and a reference dataset.

    The classification model compares test images to images in a reference
    set by their embeddings. Distances to each reference image are
    calculated and transformed into classification scores. In effect,
    the label of the highest classification score is equal to the label of the
    reference image with the lowest distance to the image to classify.

    This code is more or less the same as the code for the embedding classifier
    in the Vuurwerkverkenner-FIRE repository, which is used to evaluate the
    embedding model.

    Note: The model assumes there is a global variable 'current_app' with an attribute
    'meta_data' containing the metadata and reference embeddings.
    """

    def __init__(self,
                 model: EmbeddingModel,
                 predict_full_image: bool = True,
                 embedding_aggregate: str = 'mean',
                 class_aggregate: str = 'max',
                 distance_metric: str = 'euclidean'):
        """
        Initialize the model.

        :param model: defines the embedding model that creates the embeddings
          that are compared by this EmbeddingClassifier model
        :param predict_full_image: whether to generate one prediction/embedding
          for the full image (True) or one each for the snippets that
          constitute the image
        :param embedding_aggregate: function used to aggregate scores when the
          query image represents more than one embedding (i.e. when it is split
          into multiple snippets which each have their own embedding). Choices
          are "min", "max", "mean", "median"
        :param class_aggregate: function used to aggregate scores when more
          than one reference image is present for a class. For instance, we may
          have multiple snippets/wrappers of the same category in our reference
          class. Choices are "min", "max", "mean", "median", "mode", "first",
          "last" and "random".
        :param distance_metric: metric to compute distance
          (see: scipy.spatial.distance.cdist)
        """
        if not isinstance(model, EmbeddingModel):
            raise ValueError("Provided model is not an embedding model")
        self.model = model
        self.predict_full_image = predict_full_image
        self.distance_metric = distance_metric
        self.class_aggregate = AGGREGATORS[class_aggregate]
        self.embedding_aggregate = AGGREGATORS[embedding_aggregate]

    def predict(self, image: Image) -> Mapping[str, float]:
        if self.predict_full_image:
            snippets = [image]
        else:
            snippets = list(segment_snippets(image))

        image_embeddings = [self.model.predict(snippet) for snippet in snippets]
        classifications = [self._get_classification_scores(image_embedding.reshape(1, -1))
                           for image_embedding in image_embeddings]
        classification = {
            label: self.embedding_aggregate(
                [classification[label] for classification in classifications]
            )
            for label in self.labels
        }

        return classification

    def _get_classification_scores(self, image_embedding: np.ndarray) -> Mapping[str, float]:
        """
        Calculate the classification scores for one image embedding. Each
        reference image embedding yields a score for the corresponding
        reference label. These scores are then aggregated on the label using
        `self.class_aggregate`.

        :param image_embedding: the image embedding to predict
        :returns: a dict containing the score for each label
        """
        classification = {}

        # if there are multiple embeddings for a reference sample, aggregate
        distances = {label: cdist(image_embedding, data["embeddings"], metric=self.distance_metric)
                     for label, data in current_app.meta_data.items()}
        distances_agg = {}
        for label, d in distances.items():
            d_arr = np.array(d).flatten()
            distances_agg[label] = self.class_aggregate(d_arr)

        for label, distance in distances_agg.items():
            # Classifications have _scores_, where higher scores are usually
            # better. Since we have computed a distance, we need to convert
            # it into a score.
            #
            # The below conversion heuristic has two nice properties:
            # - smaller distances transform into larger scores
            # - distance metrics with 0 distance for a "perfect match"
            #   transform into a "perfect match" score of 1
            #
            # It is assumed here that the embeddings are normalized by the
            # model. Therefore, when L2 is used as a metric to calculate
            # the distance between two embeddings, the distance is divided
            # by 2 (= the maximum distance between two embeddings in a unit
            # hypersphere) to keep the scores consistently between 0 and 1.
            if self.distance_metric in ('l2', 'euclidean'):
                distance /= 2

            score = 1. - distance

            classification[label] = score

        return classification

    @property
    def labels(self):
        return set(current_app.meta_data.keys())
