# app1.py — Bài 1: Hello API
# pyrefly: ignore [missing-import]
from flask import Flask, jsonify

app = Flask(__name__)   

@app.route("/")
def index():    
    return jsonify({"message": "Hello, API!"}), 200

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
