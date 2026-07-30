"""Pump synthetic conversations into Postgres so the Grafana dashboard
has data to show. Inserts one conversation per second until stopped."""

import os
import random
import time
import uuid

from dotenv import load_dotenv

load_dotenv()
os.environ.setdefault("POSTGRES_HOST", "localhost")

from zoning_assistant import db  # noqa: E402

QUESTIONS = [
    "Can I build an ADU on my SF-2 lot?",
    "What's the maximum height in the GR district?",
    "Do I need a permit to pour a foundation?",
    "What are the setbacks in SF-3?",
    "Is my parcel in a flood zone?",
    "How tall can my backyard fence be?",
]

ANSWERS = [
    "Yes, one ADU is permitted by right if the lot is at least 5,750 sq ft (Section 3.1).",
    "The maximum height in GR is 60 feet (Section 2.7.1).",
    "Yes — an approved building permit and a form inspection are required first (Section 4.3).",
    "Front 25 ft, side 5 ft, rear 10 ft (Section 2.3.4).",
    "Parcels in FEMA Zone AE must elevate the finished floor 2 feet above BFE (Section 5.1).",
    "Up to 6 feet in side and rear yards, 4 feet in the front yard (Section 7.1).",
]

RELEVANCE = ["RELEVANT", "RELEVANT", "RELEVANT", "PARTLY_RELEVANT", "NON_RELEVANT"]
MODELS = ["gpt-4o-mini", "gpt-4o"]


def generate_conversation():
    q_idx = random.randrange(len(QUESTIONS))
    prompt_tokens = random.randint(600, 1400)
    completion_tokens = random.randint(80, 350)
    eval_pt, eval_ct = random.randint(150, 300), random.randint(30, 80)
    model = random.choice(MODELS)

    answer_data = {
        "answer": ANSWERS[q_idx],
        "model_used": model,
        "response_time": random.uniform(0.8, 5.0),
        "relevance": random.choice(RELEVANCE),
        "relevance_explanation": "Synthetic monitoring data.",
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": prompt_tokens + completion_tokens,
        "eval_prompt_tokens": eval_pt,
        "eval_completion_tokens": eval_ct,
        "eval_total_tokens": eval_pt + eval_ct,
        "openai_cost": random.uniform(0.0003, 0.01),
    }

    conversation_id = str(uuid.uuid4())
    db.save_conversation(conversation_id, QUESTIONS[q_idx], answer_data)

    if random.random() < 0.6:
        db.save_feedback(conversation_id, random.choice([1, 1, 1, 1, -1]))

    return conversation_id


if __name__ == "__main__":
    print("Generating synthetic conversations (Ctrl+C to stop)...")
    while True:
        cid = generate_conversation()
        print(f"inserted {cid}")
        time.sleep(1)
