from flask import Flask, jsonify, request

app = Flask(__name__)

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
        return jsonify({
            "error": "title, content and user_id are required"
        }), 400

    post = {
        "id": next_id,
        "title": title,
        "content": content,
        "user_id": user_id
    }

    posts.append(post)
    next_id += 1

    return jsonify(post), 201


if __name__ == "__main__":
    app.run(debug=True)