from types import MappingProxyType
from typing import Union

from confidence import Configuration
from confidence.models import ConfigurationSequence

from app.calculations.models.base import ClassificationModel, EmbeddingModel
from app.calculations.models.dummy import DummyModel
from app.calculations.models.embedding import EmbeddingViTModel
from app.calculations.models.embedding_classifier import EmbeddingClassifierModel

MODELS = {'dummy': DummyModel,
          'embedding_vit': EmbeddingViTModel,
          'embedding_classifier': EmbeddingClassifierModel}


def load_model(model_config: Configuration) -> Union[ClassificationModel, EmbeddingModel]:
    # get model name from config
    name = model_config['name']
    # get model parameters from config
    params = MappingProxyType(
        {k: tuple(v) if isinstance(v, ConfigurationSequence) else
         (load_model(v) if k == 'model' else v)
         for k, v in model_config.items() if k != 'name'}
    )
    # instantiate and return model instance
    return MODELS[name](**params)
