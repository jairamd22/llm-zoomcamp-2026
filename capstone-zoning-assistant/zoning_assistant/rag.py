"""RAG flow: retrieve zoning sections with minsearch, answer with an LLM.

Plain retrieve-then-answer (no agent/tool-calling — that's Project 3).
Every answer is grounded: the prompt instructs the model to answer only
from the retrieved sections and cite section numbers.
"""

import json
import os
from time import time

from openai import OpenAI

from zoning_assistant import ingest

MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
EVAL_MODEL = os.getenv("EVAL_MODEL", MODEL)

openai_client = OpenAI()

index = ingest.load_index()
parcels = ingest.load_parcels()

# Boost weights found via random search on the validation split
# (see notebooks/retrieval-eval.ipynb). Baseline (no boosts):
# Hit Rate / MRR reported in the README.
BOOST = json.loads(os.getenv("BOOST_WEIGHTS", "{}")) or {
    "section": 0.66,
    "district": 1.52,
    "category": 0.08,
    "title": 0.60,
    "text": 1.95,
}

NUM_RESULTS = int(os.getenv("NUM_RESULTS", "5"))


def search(query: str):
    return index.search(
        query=query,
        filter_dict={},
        boost_dict=BOOST,
        num_results=NUM_RESULTS,
    )


def lookup_parcel(query: str):
    """Naive parcel lookup: if the question mentions a known parcel id or
    address, attach that parcel's record as extra context."""
    q = query.lower()
    for key, record in parcels.items():
        if key in q:
            return record
    return None


prompt_template = """
You're a municipal zoning research assistant for the City of Riverbend.
Answer the QUESTION using only the facts in the CONTEXT sections below.

Rules:
- Cite the section number (e.g. "Section 3.2") for every rule you state.
- If the CONTEXT does not contain the answer, say you don't know and
  suggest the user contact the city's planning department. Do not guess.
- If PARCEL data is provided, apply the rules to that specific parcel
  (its district, lot size, flood zone, and overlays).
- This is research assistance, not legal advice; note that final
  determinations are made by the city.

QUESTION: {question}

{parcel_block}CONTEXT:
{context}
""".strip()

entry_template = """
section: {section}
district: {district}
category: {category}
title: {title}
text: {text}
""".strip()


def build_prompt(query: str, search_results: list, parcel: dict | None = None) -> str:
    context = "\n\n".join(entry_template.format(**doc) for doc in search_results)
    parcel_block = ""
    if parcel:
        parcel_block = "PARCEL:\n" + json.dumps(parcel, default=str) + "\n\n"
    return prompt_template.format(
        question=query, context=context, parcel_block=parcel_block
    ).strip()


def llm(prompt: str, model: str = MODEL):
    t0 = time()
    response = openai_client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
    )
    answer = response.choices[0].message.content
    tokens = {
        "prompt_tokens": response.usage.prompt_tokens,
        "completion_tokens": response.usage.completion_tokens,
        "total_tokens": response.usage.total_tokens,
    }
    return answer, tokens, time() - t0


evaluation_prompt_template = """
You are an expert evaluator for a RAG system that answers municipal
zoning questions. Classify the relevance of the generated answer to the
question.

Question: {question}
Generated Answer: {answer}

Analyze the content and context of the generated answer in relation to
the question and provide your evaluation in parsable JSON without using
code blocks:

{{"Relevance": "NON_RELEVANT" | "PARTLY_RELEVANT" | "RELEVANT",
  "Explanation": "[Provide a brief explanation for your evaluation]"}}
""".strip()


def evaluate_relevance(question: str, answer: str):
    prompt = evaluation_prompt_template.format(question=question, answer=answer)
    evaluation, tokens, _ = llm(prompt, model=EVAL_MODEL)
    try:
        json_eval = json.loads(evaluation)
        return json_eval["Relevance"], json_eval["Explanation"], tokens
    except (json.JSONDecodeError, KeyError):
        return "UNKNOWN", "Failed to parse evaluation", tokens


def calculate_openai_cost(model: str, tokens: dict) -> float:
    # $/1M tokens; extend for the models you actually use
    prices = {
        "gpt-4o-mini": (0.15, 0.60),
        "gpt-4o": (2.50, 10.00),
        "gpt-4.1-mini": (0.40, 1.60),
    }
    inp, out = prices.get(model, (0.0, 0.0))
    return (tokens["prompt_tokens"] * inp + tokens["completion_tokens"] * out) / 1e6


def rag(query: str, model: str = MODEL) -> dict:
    t0 = time()

    parcel = lookup_parcel(query)
    search_results = search(query)
    prompt = build_prompt(query, search_results, parcel)
    answer, tokens, _ = llm(prompt, model=model)

    relevance, explanation, eval_tokens = evaluate_relevance(query, answer)

    cost = calculate_openai_cost(model, tokens) + calculate_openai_cost(
        EVAL_MODEL, eval_tokens
    )

    return {
        "answer": answer,
        "model_used": model,
        "response_time": time() - t0,
        "relevance": relevance,
        "relevance_explanation": explanation,
        "prompt_tokens": tokens["prompt_tokens"],
        "completion_tokens": tokens["completion_tokens"],
        "total_tokens": tokens["total_tokens"],
        "eval_prompt_tokens": eval_tokens["prompt_tokens"],
        "eval_completion_tokens": eval_tokens["completion_tokens"],
        "eval_total_tokens": eval_tokens["total_tokens"],
        "openai_cost": cost,
        "retrieved_sections": [doc["section"] for doc in search_results],
    }
