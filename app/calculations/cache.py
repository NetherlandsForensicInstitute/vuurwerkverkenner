import uuid
from typing import Any

from flask import current_app


def add_to_cache(value: Any) -> str:
    key = uuid.uuid4().hex
    current_app.cache[key] = value
    return key


def get_from_cache(key: str) -> Any:
    return current_app.cache.get(key, None)
