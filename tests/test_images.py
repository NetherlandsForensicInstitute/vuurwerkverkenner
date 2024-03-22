import numpy as np
from PIL import Image

from app.calculations.models.utils import convert_PIL_image_to_numpy, min_max_normalize


def test_image_to_numpy_conversion(test_color_image: Image):
    data = convert_PIL_image_to_numpy(test_color_image, reverse_color_channels=False)
    assert np.array_equal(data[0, 0, :], list(test_color_image.getdata())[0])
    data = convert_PIL_image_to_numpy(test_color_image, reverse_color_channels=True)
    assert np.array_equal(data[0, 0, :], list(test_color_image.getdata())[0][::-1])
    assert data.dtype == np.uint8

    data_normalized = min_max_normalize(data, target_range=(-1., 1.))
    assert np.isclose(data_normalized.min(), -1.)
    assert np.isclose(data_normalized.max(), 1.)
    assert data_normalized.dtype == np.float64
