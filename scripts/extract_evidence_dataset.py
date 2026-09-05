import json
from pathlib import Path
from app.extraction.evidence_extractor import extract_candidate_evidence

INPUT_FILE = Path("data/processed/candidates.jsonl")
OUTPUT_FILE = Path("data/processed/evidence.jsonl")

total_candidates = 0
total_evidence = 0

with INPUT_FILE.open("r", encoding="utf-8") as infile, \
     OUTPUT_FILE.open("w", encoding="utf-8") as outfile:

    for line in infile:
        if not line.strip():
            continue

        candidate = json.loads(line)
        evidence = extract_candidate_evidence(candidate)

        record = {
            "candidate_id": candidate["candidate_id"],
            "evidence_count": len(evidence),
            "evidence": evidence
        }

        outfile.write(json.dumps(record, ensure_ascii=False) + "\n")

        total_candidates += 1
        total_evidence += len(evidence)

        if total_candidates % 1000 == 0:
            print(
                f"Processed candidates: {total_candidates} | "
                f"Evidence items: {total_evidence}"
            )

print("\n" + "=" * 70)
print("STEP 13.2 - FULL RESUME EVIDENCE EXTRACTION")
print("=" * 70)
print(f"Candidates processed: {total_candidates}")
print(f"Total evidence items: {total_evidence}")
print(f"Output: {OUTPUT_FILE}")
print("=" * 70)