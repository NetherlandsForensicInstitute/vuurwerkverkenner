import numpy as np
from PIL import Image

from app.calculations.models.utils import convert_pil_image_to_numpy


def test_image_to_numpy_conversion(test_color_image: Image):
    data = convert_pil_image_to_numpy(test_color_image)
    assert np.array_equal(data[0, 0, :], list(test_color_image.getdata())[0])
