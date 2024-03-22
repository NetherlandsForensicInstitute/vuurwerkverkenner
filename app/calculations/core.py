import threading
from typing import Any, Optional, Mapping, Set, Sequence, NamedTuple

from flask import current_app

from app.calculations.models.utils import convert_bytes_to_PIL_image

LOCK = threading.Lock()


class Result(NamedTuple):
    label: str
    score: float = None
    meta: Mapping[str, Any] = None


def get_results(
        query_image: Optional[bytes], query_text: Optional[str]
) -> Optional[Sequence[Result]]:
    # Warning: it is assumed here that query_image is a verified image and
    # query_text is either empty or a sanitized string, since it is not
    # this method's responsibility to clean the inputs
    if not (query_image or query_text):
        return None

    # get the labels for which the image text matches
    matches = get_text_matches(query_text)

    if query_image:
        # get the model predictions if a query image is provided
        predictions = get_predictions(image=query_image)

        # use the predicted scores
        classification_scores = tuple(
            Result(label, score) for label, score in predictions.items() if label in matches
        )
    else:
        # otherwise, use binary scores
        classification_scores = tuple(
            Result(label, 1) for label in current_app.meta_data.keys() if label in matches
        )

    # sort on descending scores
    classification_scores = sorted(
        classification_scores, key=lambda item: item.score, reverse=True
    )
    return classification_scores


def get_predictions(image: bytes) -> Mapping[str, Any]:
    """
    Get the predictions for a single image stored in raw bytes format using the model
    stored in `current_app.model`

    :param image: the raw image to get the prediction(s) for
    :returns: a mapping of labels -> predicted scores for the image
    """
    with LOCK:
        model = current_app.model
        pil_image = convert_bytes_to_PIL_image(image)
        predictions = model.predict(image=pil_image)
        return predictions


def get_text_matches(query_text: Optional[str]) -> Set[str]:
    """
    Compute the matching labels based on text on the image and the
    stored mapping between labels and text.

    :param query_text: the text on the image
    :returns: a set containing the labels that match the text on the image
    """
    if not query_text or query_text.strip() == "":
        # if no text is entered, return all labels
        return set(current_app.meta_data.keys())

    tokens = query_text.split(' ')
    matches = set(label for label, data in current_app.meta_data.items()
                  if any(all(token in wrapper["text"] for token in tokens)
                         for wrapper in data['wrappers'].values()))
    return matches
