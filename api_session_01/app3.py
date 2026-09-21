from flask import Flask, jsonify, request
from uuid import uuid4

app = Flask(__name__)

STUDENTS = []

# GET /students
@app.route("/students", methods=["GET"])
def get_students():
    return jsonify(STUDENTS), 200

# GET /students/<student_id>
@app.route("/students/<student_id>", methods=["GET"])
def get_student(student_id):
    student = next((s for s in STUDENTS if s["id"] == student_id), None)
    if not student:
        return jsonify({"error": "Không tìm thấy sinh viên"}), 404
    return jsonify(student), 200

# POST /students
@app.route("/students", methods=["POST"])
def create_student():
    body = request.get_json(silent=True) or {}
    name = body.get("name")
    if not name:
        return jsonify({"error": "name là bắt buộc"}), 400

    student = {
        "id": str(uuid4()),
        "name": name,
        "gpa": body.get("gpa", 0.0),
    }
    STUDENTS.append(student)

    return jsonify(student), 201, {"Location": f"/students/{student['id']}"}

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
