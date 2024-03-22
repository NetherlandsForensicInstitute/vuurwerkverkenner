import io
from typing import List, Iterable, Optional, Tuple

import cv2
import numpy as np
from PIL import Image


def convert_bytes_to_PIL_image(image: bytes) -> Image:
    """
    Convert the raw binary image data to a PIL Image in RGB format.

    :param image: raw binary image data
    :returns: a PIL Image in RGB format
    """
    return Image.open(io.BytesIO(image)).convert('RGB')


def convert_PIL_image_to_numpy(
        image: Image, resize: Optional[Tuple[int, int]] = None,
        reverse_color_channels: bool = True
) -> np.ndarray:
    """
    Convert a PIL Image into a numpy array with the option to also resize the image before conversion.
    The resulting array will be a numpy array with unsigned 8-bit integers.

    :param image: the PIL Image to convert
    :param resize: optional parameter for resizing the image
    :param reverse_color_channels: whether to reverse the order of the color channels in the output array
        (i.e. from 'RGB' to 'BGR' and vice versa). This is needed for instance when the trained model
        expects images in BGR color format instead of RGB
    :returns: the numpy array of type np.uint8
    """
    data = np.asarray(image.resize(size=resize) if resize else image, dtype=np.uint8)
    if reverse_color_channels:
        data = data[..., ::-1]  # swap red and blue channels
    return data


def min_max_normalize(
        image: np.ndarray, target_range: Tuple[float, float] = (-1., 1.)
) -> np.ndarray:
    """
    Map pixel intensities to a desired range by applying min-max normalization.
    By default, the target range is [-1, 1].  It is assumed that the input is a
    numpy array consisting of unsigned 8-bit integers.

    :param image: the image data to convert
    :param target_range: the desired range to map the normalized pixel intensities to
    :returns: the normalized array of type np.float32
    """
    min_val, max_val = target_range
    if min_val > max_val:
        raise ValueError("The first argument of `target_range` should be less "
                         "than or equal to the second argument")
    scale = 1. / 255.
    return np.array(scale * image * (max_val - min_val) + min_val,
                    dtype=np.float64)


def get_contours_from_image(
        image: np.ndarray, t1: int = 140, t2: int = 255, inverse: bool = False,
        morph: bool = True, hierarchy_level: int = -1
) -> List[np.ndarray]:
    """
    Compute object contours from an image using OpenCV's findContours.
    First the image is transformed to a grayscale image. Then, based
    on the provided threshold values, the image is transformed to a binary
    image from which the contours are computed.

    :param image: numpy array of type np.uint8 containing the RGB image data
    :param t1: bottom threshold value for the binary thresholding
    :param t2: upper threshold value
    :param inverse: whether to use OpenCV's inverse binary thresholding.
    This means that the binary values of the pixels after thresholding
    will be switched. For the exact mathematical definition see:
    https://docs.opencv.org/4.x/d7/d1b/group__imgproc__misc.html#ggaa9e58d2860d4afa658ef70a9b1115576a19120b1a11d8067576cc24f4d2f03754
    :param morph: whether to also apply morphological operations (e.g. closing)
    to the binary image before contour detection
    :param hierarchy_level: the hierarchy level the contours will be
    filtered on. Contours that are not contained in any other contour
    have hierarchy level -1 (i.e. outer contours have no parents).
    Contours that are contained in precisely one other contour
    have hierarchy level 0, etc.

    :returns: list of detected contours at the given hierarchy level
    """
    # preprocess and threshold image
    img_grey = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    # TODO: extend functionality to allow for dynamic thresholding?
    mode = cv2.THRESH_BINARY_INV if inverse else cv2.THRESH_BINARY
    thresh = cv2.threshold(img_grey, t1, t2, mode)[1]
    if morph:
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (50, 50))
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
    # detect contours in processed image
    contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE,
                                           cv2.CHAIN_APPROX_SIMPLE)
    # keep only contours with the specified hierarchy level
    contours = [contours[i] for i, h in enumerate(hierarchy[0])
                if h[3] == hierarchy_level]
    return contours


def get_mask_from_contours(
        contours: List[np.ndarray], shape: Tuple[int, ...]
) -> np.ndarray:
    """
    Take a list of contours and a 2D image shape, and generate a
    filled mask from these contours with the required shape.

    :param contours: the list of contours to be filled in the mask
    :param shape: the shape of the output image
    :returns: a boolean mask with the filled contours
    """
    mask = np.zeros(shape=shape, dtype=np.uint8)
    cv2.drawContours(mask, contours, -1, (255, 255, 255), thickness=cv2.FILLED)
    return mask > 0


def segment_snippets(
        image: Image, min_surface: float = 5000
) -> Iterable:
    """
    Identifies individual snippets on a white background picture and
    segments them.
    :param image: the RGB image data (of type np.uint8) to extract the snippets from
    :param min_surface: the minimum surface area of a snippet to be extracted
      and saved (as percentage of total image size)
    :returns: the individual snippet images
    """
    image = np.asarray(image, dtype=np.uint8)
    contours = get_contours_from_image(image, t1=140, t2=255,
                                       inverse=True, morph=True,
                                       hierarchy_level=-1)

    # Extract and save each contour as separate image
    for i, contour in enumerate(contours):
        x, y, w, h = cv2.boundingRect(contour)
        if h * w > min_surface:
            mask = get_mask_from_contours(contours=[contour],
                                          shape=image.data.shape[:-1])
            # create numpy views of the bounding box
            mask_slc = mask[y:y + h, x:x + w]
            img_slc = image[y:y + h, x:x + w, :]
            # create image with white background
            img_copy = np.empty(shape=(h, w, 3), dtype=np.uint8)
            img_copy.fill(255)
            # copy image data to array (paste snippet)
            img_copy[mask_slc] = img_slc[mask_slc]

            yield Image.fromarray(img_copy)
