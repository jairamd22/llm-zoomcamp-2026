# How This Project Is Built & How to Demo It

This doc has two parts: **(1) how the system is put together** — so you can
explain any file if asked — and **(2) a scripted 10-minute demo** you can run
for a grader, interviewer, or colleague. For interview Q&A drills, open
[`interview-prep.html`](interview-prep.html) in a browser.

---

## Part 1 — How it's built

### The flow of one question

```
"Can I build a granny flat on my SF-2 lot?"
        │
        ▼
POST /question  (app.py, Flask)
        │
        ▼
rag()  (zoning_assistant/rag.py)
  1. lookup_parcel()  — if the text mentions a known parcel ID/address,
     attach that parcel's record (district, lot size, flood zone)
  2. search()         — minsearch over data/zoning.csv with tuned boosts,
     returns top-5 zoning sections
  3. build_prompt()   — grounding prompt: "answer ONLY from these
     sections, cite section numbers, say I-don't-know otherwise"
  4. llm()            — OpenAI call, returns answer + token counts
  5. evaluate_relevance() — a second LLM call judges the answer:
     RELEVANT / PARTLY_RELEVANT / NON_RELEVANT
        │
        ▼
db.save_conversation()  — everything (question, answer, judge label,
tokens, cost, latency) logged to Postgres
        │
        ▼
JSON response: answer + cited sections + conversation_id
(the id lets the user POST /feedback with +1/-1)
```

### Component map

| File | What it does | One-line talking point |
|---|---|---|
| `data/zoning.csv` | 59 zoning sections — the knowledge base. One row = one code section | "Record-based chunking: the code's own Article/Section structure is the chunk boundary, so citations are defensible" |
| `data/parcels.csv` | 40 property records | "Lets answers be parcel-specific without an agent — a simple string-match lookup, injected as context" |
| `data/generate_seed_data.py` | Regenerates both CSVs | "The dataset is synthetic but modeled on Austin's LDC — the repo has zero download steps" |
| `zoning_assistant/minsearch.py` | Vendored in-memory keyword search (TF-IDF + cosine + boosts) | "Zero infra risk; the whole index rebuilds in <1s at startup" |
| `zoning_assistant/ingest.py` | Loads CSVs into the index at app startup | "Startup ingestion is a documented P1 scoping choice; scheduled pipelines are the P4 upgrade" |
| `zoning_assistant/rag.py` | Search, prompt, LLM, judge, cost tracking | "The boost weights in here aren't guesses — they came out of the tuning notebook" |
| `zoning_assistant/db.py` | Postgres schema + logging | "Every conversation is logged, feedback or not, so quality is auditable retroactively" |
| `app.py` / `cli.py` | Flask API + interactive CLI | |
| `notebooks/retrieval-eval.ipynb` | Hit Rate/MRR, baseline vs tuned, synonym-gap measurement | **The rubric heart of the project** |
| `notebooks/rag-eval.ipynb` | LLM-as-judge, 2-model comparison | |
| `notebooks/evaluation-data-generation.ipynb` | LLM-generated ground truth | |
| `grafana/provisioning/` | Auto-provisioned datasource + 7-panel dashboard | "No clicking around in Grafana — the dashboard exists the moment compose is up" |
| `generate_data.py` | Pumps synthetic conversations into Postgres | "For demoing the dashboard without burning API credits" |
| `db_prep.py` | Creates the two tables | Run once |

### The numbers to have memorized

| Metric | Baseline | Tuned | 
|---|---|---|
| Hit Rate (test, k=5) | 73.3% | **76.4%** |
| MRR (test, k=5) | 0.526 | **0.561** |

- Tuned boosts: `text=1.95, district=1.52, section=0.66, title=0.60, category=0.08`
  → "the rule body and district name matter most; the category label adds
  almost nothing once text is weighted properly."
- **Synonym gap**: ADU questions phrased as "granny flat / backyard
  cottage" hit only **~41%** vs 76% overall → *this measured gap is my
  evidence-based justification for pgvector in Project 2.*

---

## Part 2 — The 10-minute demo script

### Before the demo (one-time, ~5 min)

```bash
cp .env.example .env          # put your OPENAI_API_KEY in .env
docker-compose up -d          # app :5000, postgres :5432, grafana :3000
pipenv install --dev
pipenv run python db_prep.py  # create tables (first run only)
```

Optionally pre-warm the dashboard so it isn't empty when you open it:

```bash
pipenv run python generate_data.py   # let it run ~60s, then Ctrl+C
```

Open two things in advance: a terminal, and http://localhost:3000
(login admin/admin → dashboard "Zoning Assistant Monitoring").

### Minute 0–1 · Frame the problem

Say: *"Answering 'can I build an ADU on this lot' today means manually
cross-referencing zoning codes, parcel records, and permit rules. A wrong
assumption means a rejected permit. I built a RAG assistant that answers
in plain English — with the section number that backs it up, because in
this domain a hallucinated rule has legal consequences."*

### Minute 1–3 · Live question via the API

```bash
curl -s -X POST http://localhost:5000/question \
  -H "Content-Type: application/json" \
  -d '{"question": "Can I build a granny flat on my SF-2 lot?"}' | python -m json.tool
```

Point at two things in the response:
- the **answer cites sections** (e.g. Section 3.1, 3.2) — grounding is enforced by the prompt
- the `sections` array — exactly which records were retrieved

Then show the parcel-aware behavior:

```bash
curl -s -X POST http://localhost:5000/question \
  -H "Content-Type: application/json" \
  -d '{"question": "What can I build at parcel RB-2405?"}' | python -m json.tool
```

Say: *"It recognized the parcel ID, pulled that parcel's district, lot
size, and flood zone into the prompt, and answered for THAT property."*

Send feedback (copy the `conversation_id` from the response):

```bash
curl -s -X POST http://localhost:5000/feedback \
  -H "Content-Type: application/json" \
  -d '{"conversation_id": "<paste-id>", "feedback": 1}'
```

(Or do all of this interactively: `pipenv run python cli.py`.)

### Minute 3–6 · The evaluation story (this is where the points are)

Open `notebooks/retrieval-eval.ipynb` (results are visible without
re-running). Walk it top to bottom:

1. *"295 ground-truth questions, ~5 per section. Validation/test split so
   tuning can't overfit the reported number."*
2. *"Baseline keyword search, no boosts: 73.3% Hit Rate, 0.526 MRR."*
3. *"Random search over per-field boost weights on the validation split,
   optimizing MRR. On held-out test: 76.4% / 0.561."*
4. **The honest part — say it before they ask**: *"I also measured where
   keyword search fails: synonym-phrased ADU questions hit only ~41%.
   That measured paraphrase gap — not a hunch — is why my next project
   introduces semantic search."*

Then flip briefly to `notebooks/rag-eval.ipynb`: *"Answer quality is
judged by an LLM with three categorical labels rather than a 1–10 score —
categories are more reproducible across judge calls and map to a
decision: ship, review, reject. I compare two answering models on ~200
questions to justify the cheaper model. And the judge itself gets
hand-spot-checked — it's a proxy, not ground truth."*

### Minute 6–8 · Monitoring

Switch to the Grafana tab. Ask a couple more questions via curl/CLI (or
let `generate_data.py` run) and watch panels move. Point out, in order:

1. **Last 5 conversations** — question, answer, judge label
2. **Relevancy gauge** — LLM-as-judge labels, thresholded green/yellow/red
3. **Feedback pie** — thumbs up/down
4. **Cost + tokens + response time** time series — *"the three things an
   engineering team actually watches in production"*
5. **Model used** — supports the 2-model comparison

Say: *"Every query is logged whether or not the user leaves feedback —
feedback is sparse, so the log is what makes quality auditable. I can
re-run the judge over logged conversations retroactively."*

### Minute 8–10 · Design decisions + roadmap (close strong)

Three sentences, verbatim if you like:

- *"minsearch over a vector DB was deliberate: prove the evaluation
  methodology with zero infra risk, and let the evaluation itself surface
  the limitation — the 41% synonym gap — that justifies semantic search
  next, instead of assuming it."*
- *"Record-per-section chunking follows the code's own legal structure,
  so every citation is a real section number a human can verify."*
- *"No agent, on purpose: single-hop retrieve-then-answer doesn't need
  one. Multi-section questions are a documented failure mode here, and
  they're exactly what motivates the tool-calling agent in Project 3."*

Expect pushback? Open `interview-prep.html` — every pushback line they
might use is in there as an L2/L3 drill with the prepared answer.

### Teardown

```bash
docker-compose down          # keep Postgres data
docker-compose down -v       # wipe everything
```

---

## Common demo failure modes (check before you present)

| Symptom | Fix |
|---|---|
| `/question` returns 500 | `OPENAI_API_KEY` missing/invalid in `.env`; `docker-compose logs app` |
| `db_prep.py` connection refused | Postgres not up yet, or run with `POSTGRES_HOST=localhost` outside Docker |
| Grafana panels empty | Run `generate_data.py` for a minute; check time range is "Last 6 hours" |
| Grafana can't query | Datasource is auto-provisioned; if you changed DB credentials in `.env`, mirror them in `grafana/provisioning/datasources/datasource.yaml` |
| CLI can't connect | App must be running on :5000 first |
