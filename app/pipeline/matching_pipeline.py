import json
from functools import lru_cache
from pathlib import Path

from app.matching.candidate_job_matcher import match_candidate_to_job
from app.scoring.guardrails import apply_guardrails
from app.scoring.recommendation import (
    generate_recommendation,
    recommendation_reason,
)
from app.scoring.confidence import calculate_confidence
from app.explanation.generator import generate_explanation


def load_jsonl(path: str):
    records = []

    with Path(path).open(
        "r",
        encoding="utf-8",
    ) as file:

        for line in file:
            if line.strip():
                records.append(json.loads(line))

    return records


@lru_cache(maxsize=1)
def build_indexes():
    candidates = load_jsonl(
        "data/processed/candidates.jsonl"
    )

    evidence_records = load_jsonl(
        "data/processed/evidence.jsonl"
    )

    jobs = load_jsonl(
        "data/processed/jobs.jsonl"
    )

    requirement_records = load_jsonl(
        "data/processed/requirements.jsonl"
    )

    evidence_index = {
        item["candidate_id"]: item["evidence"]
        for item in evidence_records
    }

    requirement_index = {
        item["job_id"]: item["requirements"]
        for item in requirement_records
    }

    candidate_index = {
        item["candidate_id"]: item
        for item in candidates
    }

    job_index = {
        item["job_id"]: item
        for item in jobs
    }

    return (
        candidate_index,
        evidence_index,
        job_index,
        requirement_index,
    )


def run_match(
    candidate_id: str,
    job_id: str,
):
    (
        candidate_index,
        evidence_index,
        job_index,
        requirement_index,
    ) = build_indexes()

    if candidate_id not in candidate_index:
        raise ValueError(
            f"Candidate not found: {candidate_id}"
        )

    if job_id not in job_index:
        raise ValueError(
            f"Job not found: {job_id}"
        )

    evidence = evidence_index.get(
        candidate_id,
        [],
    )

    requirements = requirement_index.get(
        job_id,
        [],
    )

    result = match_candidate_to_job(
        candidate_id,
        job_id,
        requirements,
        evidence,
    )

    result = apply_guardrails(result)

    result["confidence"] = calculate_confidence(
        result
    )

    recommendation = generate_recommendation(
        result
    )

    result["recommendation"] = recommendation

    result["recommendation_reason"] = (
        recommendation_reason(
            result,
            recommendation,
        )
    )

    result["explanation"] = generate_explanation(
        result
    )

    result["job_title"] = job_index[
        job_id
    ]["normalized"]["title"]

    return result