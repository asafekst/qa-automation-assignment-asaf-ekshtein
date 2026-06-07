import pytest

from tests.api.constants import MISSING_POST_ID, VALID_POST_ID
from tests.api.helpers import (
    assert_created_post,
    assert_delete_accepted,
    assert_non_empty_json_array,
    assert_post_schema,
    assert_status,
    assert_updated_post,
    json_body,
    posts_url,
)

pytestmark = [pytest.mark.api, pytest.mark.smoke]


def test_get_posts_returns_list_with_valid_schema(http, api_base_url: str) -> None:
    response = http.get(posts_url(api_base_url))
    posts = assert_non_empty_json_array(response)
    assert_post_schema(posts[0])


@pytest.mark.parametrize(
    ("post_id", "expected_status"),
    [(VALID_POST_ID, 200), (MISSING_POST_ID, 404)],
    ids=["existing_post", "missing_post"],
)
def test_get_post_by_id(
    http, api_base_url: str, post_id: int, expected_status: int
) -> None:
    response = http.get(posts_url(api_base_url, post_id))
    assert_status(response, expected_status)
    if expected_status == 200:
        assert_post_schema(json_body(response))


def test_post_creates_resource_and_echoes_payload(
    http, api_base_url: str, new_post: dict
) -> None:
    response = http.post(posts_url(api_base_url), json=new_post)
    assert_created_post(response, new_post)


def test_put_updates_fields_and_delete_succeeds(
    http, api_base_url: str, updated_post: dict
) -> None:
    # Kept as one test: JSONPlaceholder is stateless — PUT/DELETE do not share real
    # server state. Combined flow documents the write lifecycle; splitting would add
    # files without stronger signal (no persistence or ordering to verify).
    put_response = http.put(posts_url(api_base_url, VALID_POST_ID), json=updated_post)
    assert_updated_post(put_response, VALID_POST_ID, updated_post)

    delete_response = http.delete(posts_url(api_base_url, VALID_POST_ID))
    assert_delete_accepted(delete_response)
