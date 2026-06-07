from typing import Any

import requests

POST_FIELDS = ("userId", "id", "title", "body")
WRITABLE_FIELDS = ("title", "body", "userId")


def posts_url(base_url: str, post_id: int | None = None) -> str:
    if post_id is None:
        return f"{base_url}/posts"
    return f"{base_url}/posts/{post_id}"


def assert_status(response: requests.Response, expected: int) -> None:
    assert response.status_code == expected, (
        f"Expected HTTP {expected}, got {response.status_code}. "
        f"Body: {response.text[:300]}"
    )


def json_body(response: requests.Response) -> Any:
    assert response.headers.get("Content-Type", "").startswith("application/json"), (
        f"Expected JSON response, got Content-Type: {response.headers.get('Content-Type')}"
    )
    return response.json()


def assert_non_empty_json_array(response: requests.Response) -> list:
    assert_status(response, 200)
    body = json_body(response)
    assert isinstance(body, list), "Response body must be a JSON array"
    assert body, "Expected at least one post in the collection"
    return body


def assert_post_schema(post: dict) -> None:
    for key in POST_FIELDS:
        assert key in post, f"Missing field: {key}"

    assert isinstance(post["userId"], int)
    assert isinstance(post["id"], int)
    assert isinstance(post["title"], str) and post["title"]
    assert isinstance(post["body"], str) and post["body"]


def assert_fields_match(actual: dict, expected: dict, fields: tuple[str, ...]) -> None:
    for field in fields:
        assert actual[field] == expected[field], (
            f"Field '{field}': expected {expected[field]!r}, got {actual[field]!r}"
        )


def assert_created_post(response: requests.Response, payload: dict) -> dict:
    assert_status(response, 201)
    created = json_body(response)
    assert_post_schema(created)
    assert_fields_match(created, payload, WRITABLE_FIELDS)
    assert created["id"] > 0, f"Expected generated id > 0, got {created['id']}"
    return created


def assert_updated_post(
    response: requests.Response, post_id: int, payload: dict
) -> dict:
    assert_status(response, 200)
    updated = json_body(response)
    assert_post_schema(updated)
    assert updated["id"] == post_id
    assert_fields_match(updated, payload, WRITABLE_FIELDS)
    return updated


def assert_delete_accepted(response: requests.Response) -> None:
    """JSONPlaceholder does not persist deletes — only HTTP acceptance is asserted."""
    assert response.status_code in (200, 204), (
        f"DELETE accepted without persistence check; got {response.status_code}"
    )
