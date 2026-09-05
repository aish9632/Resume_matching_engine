import json
from pathlib import Path

from app.extraction.jd_requirement_extractor import (
    extract_job_requirements,
)

INPUT_FILE = Path("data/processed/jobs.jsonl")
OUTPUT_FILE = Path("data/processed/requirements.jsonl")

total_jobs = 0
total_requirements = 0

with INPUT_FILE.open("r", encoding="utf-8") as infile, \
     OUTPUT_FILE.open("w", encoding="utf-8") as outfile:

    for line in infile:
        if not line.strip():
            continue

        job = json.loads(line)

        requirements = extract_job_requirements(job)

        record = {
            "job_id": job["job_id"],
            "job_title": job["normalized"]["title"],
            "requirement_count": len(requirements),
            "requirements": requirements,
        }

        outfile.write(
            json.dumps(
                record,
                ensure_ascii=False
            ) + "\n"
        )

        total_jobs += 1
        total_requirements += len(requirements)

        if total_jobs % 100 == 0:
            print(
                f"Processed jobs: {total_jobs} | "
                f"Requirements: {total_requirements}"
            )

print("\n" + "=" * 70)
print("STEP 14.3 - FULL JD REQUIREMENT EXTRACTION")
print("=" * 70)
print(f"Jobs processed: {total_jobs}")
print(f"Total requirements: {total_requirements}")
print(f"Output: {OUTPUT_FILE}")
print("=" * 70)

assert total_jobs == 1167, (
    f"Expected 1167 jobs, got {total_jobs}"
)

assert total_requirements > 0, (
    "No requirements were extracted"
)