from flask import Flask, jsonify, request

# pyrefly: ignore [missing-import]
from errors import ProblemError, register_error_handlers

app = Flask(__name__)

# Đăng ký error handlers
register_error_handlers(app)


posts = [
    {
        "id": 1,
        "title": "First post",
        "content": "Hello REST API",
        "user_id": 1
    }
]

next_id = 2


# GET /api/v1/posts
@app.get("/api/v1/posts")
def get_posts():
    return jsonify({
        "data": posts,
        "total": len(posts)
    }), 200


# POST /api/v1/posts
@app.post("/api/v1/posts")
def create_post():
    global next_id

    data = request.get_json(silent=True) or {}

    title = (data.get("title") or "").strip()
    content = (data.get("content") or "").strip()
    user_id = data.get("user_id")

    if not title or not content or user_id is None:
        raise ProblemError(
            status=400,
            title="Bad Request",
            detail="title, content and user_id are required"
        )

    post = {
        "id": next_id,
        "title": title,
        "content": content,
        "user_id": user_id
    }

    posts.append(post)
    next_id += 1

    return jsonify(post), 201


# GET một post
@app.get("/api/v1/posts/<int:post_id>")
def get_post(post_id):

    post = next(
        (p for p in posts if p["id"] == post_id),
        None
    )

    if post is None:
        raise ProblemError(
            status=404,
            title="Post not found",
            detail=f"Post with id {post_id} does not exist.",
            type_url="https://api.example.com/problems/post-not-found"
        )

    return jsonify(post), 200


# Route cố ý gây lỗi 500 để test
@app.get("/api/v1/test-error")
def test_error():
    result = 1 / 0
    return jsonify(result)


if __name__ == "__main__":
    app.run(debug=True)