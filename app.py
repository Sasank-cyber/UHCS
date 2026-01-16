from datetime import datetime

from flask import Flask, jsonify, render_template, request

from model import *

app = Flask(__name__)

DATA = []  # in-memory (swap with DB later)


from datetime import datetime


def create_complaint(data):
    return {
        "id": None,  # assigned later
        "student_name": data["student_name"],
        "hostel_block": data["hostel_block"],
        "room_number": data["room_number"],
        "category": data["complaint_category"],
        "description": data["complaint_description"],
        "status": "pending",
        "priority": None,
        "created_at": datetime.utcnow().isoformat(),
    }


@app.route("/")
def index():
    return render_template("index.html")


# ---------- Attendance ----------
@app.route("/api/attendance", methods=["POST"])
def mark_attendance():
    data = request.json
    record = {"type": "attendance", **data, "created_at": datetime.utcnow().isoformat()}
    DATA.append(record)
    return jsonify({"ok": True})


@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.get_json()
    text = data.get("text", "")

    if not text.strip():
        return jsonify({"error": "Empty text"}), 400

    scores = output(text)
    priority_score = float(ranking(scores))

    # Category prediction
    category = predict_category(text)

    # Priority mapping (you can tune this)
    if priority_score > 0.75:
        priority = "critical"
    elif priority_score > 0.55:
        priority = "high"
    elif priority_score > 0.35:
        priority = "medium"
    else:
        priority = "low"

    return jsonify(
        {
            "priority": priority,
            "priority_score": round(priority_score, 3),
            "category": category["category"],
            "confidence": category["confidence"],
        }
    )


if __name__ == "__main__":
    app.run(debug=True)


@app.route("/api/complaint", methods=["POST"])
def submit_complaint():
    data = request.json

    print("📩 New Complaint Received:")
    print(data)
    print("-" * 40)

    return jsonify({"ok": True})


# ---------- Fetch all ----------
@app.route("/api/data")
def get_data():
    return jsonify(DATA)


if __name__ == "__main__":
    app.run(debug=True)
    print(DATA)
