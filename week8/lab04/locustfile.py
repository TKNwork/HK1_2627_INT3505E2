"""Books API load tasks for Lab 4."""
import itertools
import random

from locust import HttpUser, between, task

_counter = itertools.count(1)


class BooksUser(HttpUser):
    wait_time = between(1, 3)

    @task(3)
    def list_books(self):
        self.client.get("/books", name="GET /books")

    @task(2)
    def read_book(self):
        book_id = random.randint(1, 50)
        with self.client.get(
            f"/books/{book_id}", name="GET /books/{id}", catch_response=True
        ) as response:
            # Expected 404 (random id absent) is not an operational failure.
            if response.status_code in (200, 404):
                response.success()
            else:
                response.failure(f"Unexpected status {response.status_code}")

    @task(1)
    def create_book(self):
        unique = next(_counter)
        self.client.post(
            "/books",
            json={"title": f"Load test {unique}", "author": "locust"},
            name="POST /books",
        )

    @task(1)
    def search_by_year(self):
        year = random.randint(2000, 2025)
        with self.client.get(
            "/books",
            params={"year": year},
            name="GET /books?year",
            catch_response=True,
        ) as response:
            # Simulate a failure in Locust while preserving the real HTTP status.
            if response.status_code == 200 and random.random() < 0.01:
                response.failure("Simulated HTTP 500 (client-side)")
