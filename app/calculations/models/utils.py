import io

import numpy as np
from PIL import Image
from transformers import ViTConfig


def convert_bytes_to_pil_image(image: bytes) -> Image:
    """
    Convert the raw binary image data to a PIL Image in RGB format.

    :param image: raw binary image data
    :returns: a PIL Image in RGB format
    """
    return Image.open(io.BytesIO(image)).convert('RGB')


def convert_pil_image_to_numpy(image: Image, resize: tuple[int, int] | None = None) -> np.ndarray:
    """
    Convert a PIL Image in RGB format into a numpy array, with the option to also resize the image before conversion.
    The resulting array will be a numpy array with unsigned 8-bit integers.

    :param image: the PIL Image to convert
    :param resize: optional parameter for resizing the image
    :returns: the numpy array of type np.uint8
    """
    data = np.asarray(image.resize(size=resize) if resize else image, dtype=np.uint8)
    return data


def get_vit_model_name(model_size: str, patch_size: int) -> str:
    """Build the model name from a given model size and patch size."""
    if model_size not in ('base', 'large', 'huge'):
        raise ValueError('`model_size` must be one of "base", "large", or "huge"')
    if patch_size not in (14, 16, 32):
        raise ValueError('`patch_size` must be one of 14, 16, or 32')
    if model_size == "huge" and patch_size != 14:
        raise ValueError('`patch_size` must be 14 for model_size="huge"')
    if model_size != "huge" and patch_size == 14:
        raise ValueError(f'`patch_size` must be 16 or 32 for model_size="{model_size}"')

    return f'google/vit-{model_size}-patch{patch_size}-224-in21k'


def build_vit_configuration(model_size: str, patch_size: int, force_download: bool, **kwargs) -> ViTConfig:
    """Build a ViTConfig instance."""
    # get the model name for this configuration
    model_name = get_vit_model_name(model_size, patch_size)
    # build custom configuration
    config = ViTConfig.from_pretrained(model_name) if force_download else ViTConfig(patch_size=patch_size)
    config.update(
        {
            **kwargs,
            'model_name': model_name,
            'do_rescale': True,  # force rescaling the data from [0, 255] to [-1, 1]
        }
    )
    return config
