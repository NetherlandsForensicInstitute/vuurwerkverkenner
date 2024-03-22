from app.calculations.cache import add_to_cache, get_from_cache


def test_add_and_get(client):
    object_id = add_to_cache("Some value")
    assert get_from_cache(object_id) == "Some value"
    assert get_from_cache('Non existent') is None


def test_full_cache_oldest_removed(client):
    """
    Check if the most recently requested elements are kept and the least recently requested removed
    in case of a full cache.
    """
    first_object = "Add me first!"
    second_object = "Add me second!"
    third_object = "Add me third!"

    first_object_id = add_to_cache(first_object)
    second_object_id = add_to_cache(second_object)

    assert get_from_cache(first_object_id) == first_object
    assert get_from_cache(second_object_id) == second_object

    third_object_id = add_to_cache(third_object)
    assert get_from_cache(first_object_id) is None
    assert get_from_cache(second_object_id) == second_object
    assert get_from_cache(third_object_id) == third_object

    # Now make sure the second object is requested most recently and fill the cache again
    assert get_from_cache(second_object_id) == second_object
    first_object_id = add_to_cache(first_object)
    assert get_from_cache(first_object_id) == first_object
    assert get_from_cache(second_object_id) == second_object
    assert get_from_cache(third_object_id) is None
