"""Interactive CLI for manual testing of the assistant.

Usage:
    python cli.py                 # type your own questions
    python cli.py --random        # sample questions from the ground truth
"""

import argparse
import json
import random
import uuid

import pandas as pd
import questionary
import requests

BASE_URL = "http://localhost:5000"


def ask_question(url, question):
    data = {"question": question}
    response = requests.post(url, json=data)
    return response.json()


def send_feedback(url, conversation_id, feedback):
    data = {"conversation_id": conversation_id, "feedback": feedback}
    response = requests.post(url, json=data)
    return response.status_code


def main():
    parser = argparse.ArgumentParser(description="Zoning assistant CLI")
    parser.add_argument(
        "--random", action="store_true",
        help="Sample questions from the ground-truth dataset",
    )
    args = parser.parse_args()

    questions = None
    if args.random:
        df = pd.read_csv("data/ground-truth-retrieval.csv")
        questions = df["question"].tolist()

    print("Welcome to the Property & Zoning Research Assistant.")
    print("Type 'exit' or press Ctrl+C to quit.\n")

    while True:
        if questions:
            question = random.choice(questions)
            print(f"Q: {question}")
        else:
            question = questionary.text("Your zoning question:").ask()

        if question is None or question.strip().lower() == "exit":
            break

        response = ask_question(f"{BASE_URL}/question", question)
        print(json.dumps(response, indent=2))

        conversation_id = response.get("conversation_id")
        if conversation_id:
            feedback = questionary.select(
                "How was the answer?",
                choices=["+1 (good)", "-1 (bad)", "skip"],
            ).ask()
            if feedback and feedback != "skip":
                score = 1 if feedback.startswith("+1") else -1
                status = send_feedback(f"{BASE_URL}/feedback", conversation_id, score)
                print(f"Feedback sent (status {status})\n")

        if questions:
            cont = questionary.confirm("Ask another random question?").ask()
            if not cont:
                break


if __name__ == "__main__":
    main()
