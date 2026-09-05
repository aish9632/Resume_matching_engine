import json
from pathlib import Path

from app.extraction.evidence_extractor import (
    extract_candidate_evidence,
)


ROOT = Path(__file__).resolve().parents[1]

candidate_file = (
    ROOT
    / "data"
    / "processed"
    / "candidates.jsonl"
)


with candidate_file.open("r", encoding="utf-8") as f:
    candidate = json.loads(f.readline())


evidence = extract_candidate_evidence(candidate)


print("=" * 70)
print("STEP 13 - RESUME EVIDENCE EXTRACTION TEST")
print("=" * 70)

print(f"Candidate: {candidate['candidate_id']}")
print(f"Evidence items: {len(evidence)}")

print("\nFirst 10 evidence items:\n")

for item in evidence[:10]:
    print(
        f"[{item['evidence_strength']}] "
        f"{item['source_type']} | "
        f"{item['action']} | "
        f"{item['status']} | "
        f"{item['text']}"
    )

assert len(evidence) > 0

for item in evidence:
    assert "evidence_id" in item
    assert "candidate_id" in item
    assert "text" in item
    assert "status" in item
    assert "evidence_strength" in item

print("\nPASS: Evidence extraction is working.")