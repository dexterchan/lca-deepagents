# python/m4/m4.3_run_manuscript.py
"""Run the manuscript agent, then self-check its findings against the known
seeded corruptions in data/epic_corpus_key.json, an immediate, exact way to
see whether the workflow's book-by-book dispatch actually covered everything.

This check is for your own feedback while working through the lab, not a
submitted grade: the key ships openly alongside the corpus.
"""

import json
import uuid
from pathlib import Path

from m4_3_manuscript_agent import agent

DATA_DIR = Path(__file__).resolve().parent / "data"

run_id = uuid.uuid4()
print(f"run with run_id/trace_id: {run_id}")
result = agent.invoke(
    {
        "messages": [{
            "role": "user",
            "content": "Run a workflow to find every corrupted sentence in the manuscript.",
        }]
    },
    config={
        "recursion_limit": 200,
        "metadata": {"trace_id": str(run_id)},
        "run_name": "manuscript_run",
        "run_id": run_id,
    },
)

report = result["messages"][-1].content
print(report)

seeded = json.loads((DATA_DIR / "epic_corpus_key.json").read_text())
seeded_sentences = {entry["sentence"] for entry in seeded}
found_sentences = {s for s in seeded_sentences if s in report}

missed = seeded_sentences - found_sentences
print(f"\nSelf-check: {len(found_sentences)}/{len(seeded_sentences)} seeded corruptions appear in the report.")
if missed:
    print("Missed:")
    for s in sorted(missed):
        print(f"  - {s}")
