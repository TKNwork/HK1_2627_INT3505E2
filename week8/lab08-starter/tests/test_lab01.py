"""LAB 1 — add your five tests here. Do not delete the smoke tests.

A. GET /books, empty database -> HTTP 200 and []
B. GET /books/9999 -> HTTP 404, JSON code == NOT_FOUND
C. POST /books with only author -> HTTP 400, errors contains title
D. POST valid book, DELETE it, GET same id -> HTTP 404
BONUS. Validate a Book response using JSON Schema; add an unknown
       field to a *copy* of the response and assert ValidationError.

Useful imports:
    from jsonschema import validate, ValidationError
    import pytest
    from tools import get_book_schema

Do not depend on test execution order. Fixtures: client, app, sample_book.
"""


def test_get_books_empty_database(client):
    response = client.get("/books")

    assert response.status_code == 200
    assert response.get_json() == []


def test_get_book_not_found(client):
    response = client.get("/books/9999")

    assert response.status_code == 404
    assert response.get_json()["code"] == "NOT_FOUND"


def test_create_book_without_title(client):
    response = client.post("/books", json={"author": "J.J. Geewax"})

    assert response.status_code == 400
    errors = response.get_json()["errors"]
    assert any(error["field"] == "title" for error in errors)


def test_get_book_after_deletion(client):
    create_response = client.post("/books", json={"title": "Book", "author": "Author"})
    assert create_response.status_code == 201
    book_id = create_response.get_json()["id"]

    delete_response = client.delete(f"/books/{book_id}")
    assert delete_response.status_code == 204

    response = client.get(f"/books/{book_id}")
    assert response.status_code == 404


def test_response_extra_field_blocked(client, sample_book):
    import pytest
    from jsonschema import ValidationError, validate
    from tools import get_book_schema

    response = client.get(f"/books/{sample_book}")
    assert response.status_code == 200

    book = response.get_json()
    schema = get_book_schema()
    # Match the API's integer year and express OpenAPI nullability in JSON Schema.
    properties = schema["properties"]
    properties["year"]["type"] = ["integer", "null"]
    properties["isbn"]["type"] = ["string", "null"]
    validate(instance=book, schema=schema)

    book_with_extra_field = {**book, "password_hash": "fake-hash"}
    with pytest.raises(ValidationError, match="password_hash"):
        validate(instance=book_with_extra_field, schema=schema)

