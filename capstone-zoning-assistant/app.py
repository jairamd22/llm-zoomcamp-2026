"""Flask API for the Property & Zoning Research Assistant."""

import uuid

from flask import Flask, jsonify, request

from zoning_assistant import db
from zoning_assistant.rag import rag

app = Flask(__name__)


@app.route("/question", methods=["POST"])
def handle_question():
    data = request.json or {}
    question = data.get("question")

    if not question:
        return jsonify({"error": "No question provided"}), 400

    conversation_id = str(uuid.uuid4())
    answer_data = rag(question)

    db.save_conversation(
        conversation_id=conversation_id,
        question=question,
        answer_data=answer_data,
    )

    return jsonify({
        "conversation_id": conversation_id,
        "question": question,
        "answer": answer_data["answer"],
        "sections": answer_data["retrieved_sections"],
    })


@app.route("/feedback", methods=["POST"])
def handle_feedback():
    data = request.json or {}
    conversation_id = data.get("conversation_id")
    feedback = data.get("feedback")

    if not conversation_id or feedback not in [1, -1]:
        return jsonify({"error": "Invalid input"}), 400

    db.save_feedback(conversation_id=conversation_id, feedback=feedback)
    return jsonify({"message": f"Feedback received: {feedback}"})


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
