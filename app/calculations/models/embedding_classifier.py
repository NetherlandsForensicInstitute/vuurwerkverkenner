from collections import defaultdict
from collections.abc import Mapping

import numpy as np
from scipy.spatial.distance import cdist
from torch import no_grad

from app.calculations.models.base import ClassificationModel, EmbeddingModel


class EmbeddingClassifier(ClassificationModel):
    def __init__(
        self,
        model: EmbeddingModel,
        metric: str = 'cosine',
        class_aggregator: np.ufunc = np.min,
    ):
        """
        Create an instance of EmbeddingClassifier.

        :param model: The embedding model, which should be an instance of EmbeddingModel
        :param metric: The metric used for computing the distances between the embeddings. Possible values are
            'euclidean' or 'cosine'
        :param class_aggregator: A numpy function for aggregating the distances per class (i.e. np.min or np.mean etc.)
        """
        if not model:
            raise ValueError('`EmbeddingClassifierModel` requires an embedding model')
        if metric not in ('cosine', 'euclidean'):
            raise ValueError('metric must be one of "cosine" or "euclidean"')

        self.model = model
        self.metric = metric
        self.class_aggregator = class_aggregator
        self.reference_embeddings = None
        self.model.eval()

    def predict(self, instance: np.ndarray) -> dict[tuple[str, str], float]:
        """Predict the labels for a single instance."""
        if not self.reference_embeddings:
            raise ValueError('Reference embeddings are not set.')

        with no_grad():
            # compute the embeddings for the input batch
            val_embeddings = self.model(instance).cpu().numpy()
        scores = []
        for category, label in self.reference_embeddings:
            # compute the distances between the query embedding and the reference embeddings for this label
            # TODO: benchmark this against cdist() on all embeddings at the same time
            dists = cdist(val_embeddings, self.reference_embeddings[(category, label)], metric=self.metric)
            scores.extend(self.class_aggregator(dists, axis=-1))

        scores = np.asarray(scores)
        scores = 1 - scores / 2.0  # ensure 0. <= scores <= 1.

        # return the predicted scores
        return dict(zip(tuple(self.reference_embeddings), scores.tolist()))

    def update_embeddings(self, meta_data: Mapping[str, Mapping[str, np.ndarray]]):
        """
        Load the embeddings from the meta_data and store it in the cache of this model class.
        """
        ref_embeddings = defaultdict()
        for category, category_data in meta_data.items():
            for label, label_data in category_data.items():
                ref_embeddings[(category, label)] = label_data['embeddings']
        self.reference_embeddings = ref_embeddings
