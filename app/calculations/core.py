import threading
from collections.abc import Mapping
from functools import cache
from typing import Any, NamedTuple

from flask import current_app

from app.calculations.models.utils import convert_bytes_to_pil_image, convert_pil_image_to_numpy
from app.requests.validate import process_query_text

LOCK = threading.Lock()


class Result(NamedTuple):
    label: str
    category: str
    score: float = None
    meta: Mapping[str, Any] = None


def get_search_results(
    query_image: bytes | None, query_text: str | None, text_filter: bool = False, include_digits: bool = False
) -> tuple[list[Result], list[str]]:
    """
    Get the search results for a given query image and query text. If a query image is provided, sort the results based
    on the model predictions. Else, if a query_text is provided, sort based on the presence of the entire query text on
    the wrapper. If both the query text and the query image are not provided, use an unsorted list of results.
    Subsequently, if text_filter is True, filter the list of results based on the presence of all individual tokens in
    the query on the wrapper text.
    """
    errors = []
    if query_text:
        # cleanup the query text
        query_text, error = process_query_text(query_text=query_text, include_digits=include_digits)
        errors.extend(error)

    if query_image:
        results = get_sorted_results_by_image(query_image=query_image)
    elif query_text:
        results = get_sorted_results_by_query_text(query_text=query_text)
    else:
        results = get_unsorted_results()

    # filter on presence query_text tokens
    if text_filter and query_text:
        results = filter_results(query_text, results)
    return results, errors


def filter_results(query_text: str, results: list[Result]) -> list[Result]:
    """Filter the results based on the presence of all individual tokens of the query text in the wrapper text."""
    tokens = query_text.split(' ')
    results = [
        result
        for result in results
        if all(token in current_app.meta_data[result.category][result.label]['wrappers']['text'] for token in tokens)
    ]
    return results


def get_sorted_results_by_image(query_image: bytes) -> list[Result]:
    """Get the results sorted by classification score. Here it is assumed that `query_image` is a verified image."""
    # get the model predictions for a query image
    predictions = get_model_predictions(image=query_image)
    # use the predicted scores
    classification_scores = tuple(
        Result(category=category, label=label, score=score) for (category, label), score in predictions.items()
    )
    # sort on descending scores
    classification_scores = sorted(classification_scores, key=lambda item: item.score, reverse=True)
    return classification_scores


def get_sorted_results_by_query_text(query_text: str) -> list[Result]:
    """Get the results sorted by the presence of the complete query text in the wrapper text."""
    results = get_unsorted_results()
    return list(
        sorted(
            results,
            key=lambda x: query_text in current_app.meta_data[x.category][x.label]['wrappers']['text'],
            reverse=True,
        )
    )


@cache
def get_unsorted_results() -> list[Result]:
    """Return all unsorted entries with score = 1."""
    return [
        Result(category=category, label=label, score=1)
        for category, data in current_app.meta_data.items()
        for label in data
    ]


def get_model_predictions(image: bytes) -> Mapping[str, float]:
    """
    Get the predictions for a single image stored in raw bytes format using the model stored in `current_app.model`.

    :param image: the raw image to get the prediction(s) for
    :returns: a mapping of labels -> predicted scores for the image
    """
    with LOCK:
        model = current_app.model
        image = convert_pil_image_to_numpy(convert_bytes_to_pil_image(image))
        predictions = model.predict(instance=image)
        return predictions


def filter_articles_in_category_on_text(
    category: str, articles: dict[str, Any], query_text: str | None
) -> dict[str, Any]:
    """
    Filter articles in a category on the query text. Here it is assumed that `query_text` is a sanitized string.

    :param category: The category name.
    :param articles: A dictionary of articles where the keys are the labels within a category.
    :param query_text: the text on the image which is assumed to be sanitized by app.requests.validate.clean_text.
    :returns: a filtered dictionary containing only items that match the query text.
    """
    tokens = query_text.split(' ')
    return {
        label: articles[label]
        for label in articles
        if all(token in current_app.meta_data[category][label]['wrappers']['text'] for token in tokens)
    }
