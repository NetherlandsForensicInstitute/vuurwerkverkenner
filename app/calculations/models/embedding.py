import numpy as np
import torch
import torch.nn.functional as F  # noqa: N812
from pydantic import BaseModel
from torch import nn
from transformers import ViTImageProcessor, ViTModel

from app.calculations.models.base import EmbeddingModel
from app.calculations.models.utils import build_vit_configuration


class ViTModelConfig(BaseModel):
    model_size: str
    patch_size: int
    image_size: int
    embedding_size: int
    add_pooling_layer: bool
    mean_pooling: bool
    device: str
    force_download: bool


class ViTEmbeddingModel(EmbeddingModel):
    def __init__(self, config: ViTModelConfig):
        """Build a PyTorch embedding model with the Vision Transformer as backbone."""
        super().__init__()
        self.config = build_vit_configuration(
            model_size=config.model_size,
            patch_size=config.patch_size,
            image_size=config.image_size,
            embedding_size=config.embedding_size,
            add_pooling_layer=config.add_pooling_layer,
            mean_pooling=config.mean_pooling,
            device=config.device,
            force_download=config.force_download,
        )
        # build the pretrained modified encoder model
        self.vit = (
            ViTModel.from_pretrained(
                pretrained_model_name_or_path=self.config.model_name,
                config=self.config,
                add_pooling_layer=self.config.add_pooling_layer,
                ignore_mismatched_sizes=True,  # partially load the weights
            )
            if config.force_download
            else ViTModel(config=self.config, add_pooling_layer=self.config.add_pooling_layer)
        )
        # attach embedding head
        self.projector = nn.Linear(in_features=self.config.hidden_size, out_features=self.config.embedding_size)
        # initialize weights
        nn.init.xavier_uniform_(self.projector.weight)
        # move the encoder model to cpu/gpu
        self.to(self.config.device)
        # build the preprocessor for this model
        self.processor = (
            ViTImageProcessor.from_pretrained(self.config.model_name) if config.force_download else ViTImageProcessor()
        )
        # update input size
        self.processor.size = {'height': self.config.image_size, 'width': self.config.image_size}

    def forward(self, images: np.ndarray | torch.Tensor) -> torch.Tensor:
        """Forward pass."""
        inputs = self.processor(images, return_tensors="pt").to(self.config.device)
        outputs = self.vit(**inputs)
        if self.config.add_pooling_layer:
            # option 1: feed the (non-linear) pooler output to the linear layer
            embedding = outputs.pooler_output
        elif self.config.mean_pooling:
            # option 2: apply mean pooling across the patch embeddings excluding the CLS token
            embedding = outputs.last_hidden_state[:, 1:, :].mean(dim=1)
        else:
            # option 3: feed the raw CLS token to the linear layer
            embedding = outputs.last_hidden_state[:, 0, :]  # get the CLS token
        return F.normalize(self.projector(embedding), p=2, dim=1)  # apply L2 normalization after projection

    @property
    def input_size(self) -> int:
        return self.config.image_size

    @property
    def embedding_size(self) -> int:
        return self.config.embedding_size
