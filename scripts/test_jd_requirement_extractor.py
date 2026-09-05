import json

from app.extraction.jd_requirement_extractor import (
    extract_job_requirements,
)


INPUT_FILE = "data/processed/jobs.jsonl"


with open(INPUT_FILE, "r", encoding="utf-8") as file:
    job = json.loads(file.readline())


requirements = extract_job_requirements(job)


print("=" * 70)
print("STEP 14 - JD REQUIREMENT EXTRACTION TEST")
print("=" * 70)

print(f"Job: {job['job_id']}")
print(f"Title: {job['normalized']['title']}")
print(f"Requirements extracted: {len(requirements)}")
print()

for index, requirement in enumerate(
    requirements[:10],
    start=1,
):
    print(
        f"[{index}] "
        f"{requirement['type']} | "
        f"{requirement['importance']} | "
        f"{requirement['canonical_concept']}"
    )
    print(f"    Text: {requirement['text']}")
    print(f"    Evidence: {requirement['source_text'][:150]}")
    print()

assert requirements, "No JD requirements extracted"

for requirement in requirements:
    assert "requirement_id" in requirement
    assert "type" in requirement
    assert "importance" in requirement
    assert "canonical_concept" in requirement
    assert "source_text" in requirement
    assert "confidence" in requirement

print("PASS: JD requirement extraction is working.")