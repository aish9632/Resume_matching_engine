import argparse
import ast
import json
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

RESUME_FILE = ROOT / "data" / "raw" / "resume_ranking" / "resume_data_for_ranking.csv"
JOB_FILE = ROOT / "data" / "raw" / "job_skill_set" / "all_job_post.csv"

INTERIM_DIR = ROOT / "data" / "interim"
PROCESSED_DIR = ROOT / "data" / "processed"


SCHEMA_VERSION = "0.1.0"


def clean_text(value):
    """Normalize text while preserving meaning."""
    if value is None or pd.isna(value):
        return ""

    text = str(value)
    text = unicodedata.normalize("NFKC", text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def normalize_text(value):
    """Lowercase normalized representation."""
    text = clean_text(value)
    return text.lower()


def parse_list_like(value):
    """
    Parse Python-list strings such as:
    "['Python', 'React', 'Docker']"

    Falls back safely to newline-separated values.
    """
    text = clean_text(value)

    if not text:
        return []

    try:
        parsed = ast.literal_eval(text)

        if isinstance(parsed, list):
            return [
                clean_text(item)
                for item in parsed
                if clean_text(item)
            ]

        if isinstance(parsed, tuple):
            return [
                clean_text(item)
                for item in parsed
                if clean_text(item)
            ]

    except (ValueError, SyntaxError):
        pass

    # Newline-separated values
    if "\n" in text:
        return [
            clean_text(item)
            for item in text.split("\n")
            if clean_text(item)
        ]

    return [text]


def normalize_list(values):
    """Normalize list values without merging concepts."""
    result = []

    for value in values:
        normalized = normalize_text(value)

        if normalized and normalized not in result:
            result.append(normalized)

    return result


def build_candidate(row, index):
    candidate_id = f"C_RANK_{index:06d}"
    source_record_id = f"R_RANK_{index:06d}"

    raw = {
        "career_objective": clean_text(row.get("career_objective")),
        "skills": clean_text(row.get("skills")),
        "responsibilities": clean_text(row.get("responsibilities")),
        "positions": clean_text(row.get("positions")),
        "role_positions": clean_text(row.get("role_positions")),
        "professional_company_names": clean_text(
            row.get("professional_company_names")
        ),
        "educational_institution_name": clean_text(
            row.get("educational_institution_name")
        ),
        "degree_names": clean_text(row.get("degree_names")),
        "major_field_of_studies": clean_text(
            row.get("major_field_of_studies")
        ),
        "passing_years": clean_text(row.get("passing_years")),
        "educational_results": clean_text(
            row.get("educational_results")
        ),
        "certification_providers": clean_text(
            row.get("certification_providers")
        ),
        "certification_skills": clean_text(
            row.get("certification_skills")
        ),
        "locations": clean_text(row.get("locations")),
        "related_skils_in_job": clean_text(
            row.get("related_skils_in_job")
        ),
    }

    skills = parse_list_like(row.get("skills"))
    responsibilities = parse_list_like(row.get("responsibilities"))
    positions = parse_list_like(row.get("positions"))
    role_positions = parse_list_like(row.get("role_positions"))
    companies = parse_list_like(row.get("professional_company_names"))
    certifications = parse_list_like(row.get("certification_skills"))
    majors = parse_list_like(row.get("major_field_of_studies"))
    related_job_skills = parse_list_like(
        row.get("related_skils_in_job")
    )

    normalized = {
        "skills": normalize_list(skills),
        "responsibilities": normalize_list(responsibilities),
        "positions": normalize_list(positions),
        "role_positions": normalize_list(role_positions),
        "companies": normalize_list(companies),
        "education": {
            "institutions": normalize_list(
                parse_list_like(row.get("educational_institution_name"))
            ),
            "degrees": normalize_list(
                parse_list_like(row.get("degree_names"))
            ),
            "majors": normalize_list(majors),
            "passing_years": normalize_list(
                parse_list_like(row.get("passing_years"))
            ),
        },
        "certifications": normalize_list(certifications),
        "related_job_skills": normalize_list(related_job_skills),
    }

    return {
        "candidate_id": candidate_id,
        "source_record_id": source_record_id,
        "source_dataset": "resume_data_for_ranking",
        "raw": raw,
        "normalized": normalized,
    }


def build_job(row, index):
    source_job_id = row.get("job_id")

    if pd.isna(source_job_id):
        source_job_id = index

    job_id = f"J_JSS_{index:06d}"

    raw = {
        "source_job_id": int(source_job_id)
        if str(source_job_id).isdigit()
        else str(source_job_id),
        "category": clean_text(row.get("category")),
        "job_title": clean_text(row.get("job_title")),
        "job_description": clean_text(row.get("job_description")),
        "job_skill_set": clean_text(row.get("job_skill_set")),
    }

    skills = parse_list_like(row.get("job_skill_set"))

    normalized = {
        "category": normalize_text(row.get("category")),
        "title": normalize_text(row.get("job_title")),
        "skills": normalize_list(skills),
        "description": normalize_text(row.get("job_description")),
    }

    return {
        "job_id": job_id,
        "source_dataset": "job_skill_set",
        "raw": raw,
        "normalized": normalized,
    }


def build_resume_job_pair(row, index):
    pair_id = f"P_RANK_{index:06d}"
    candidate_id = f"C_RANK_{index:06d}"

    skills = parse_list_like(row.get("skills_required"))
    responsibilities = parse_list_like(row.get("responsibilities.1"))

    reference_score = row.get("matched_score")

    if pd.isna(reference_score):
        reference_score = None
    else:
        reference_score = float(reference_score)

    raw = {
        "job_position_name": clean_text(row.get("job_position_name")),
        "education_requirements": clean_text(
            row.get("educationaL_requirements")
        ),
        "experience_requirement": clean_text(
            row.get("experiencere_requirement")
        ),
        "age_requirement": clean_text(row.get("age_requirement")),
        "skills_required": clean_text(row.get("skills_required")),
        "responsibilities": clean_text(row.get("responsibilities.1")),
    }

    normalized = {
        "job_title": normalize_text(row.get("job_position_name")),
        "education_requirements": normalize_text(
            row.get("educationaL_requirements")
        ),
        "experience_requirement": normalize_text(
            row.get("experiencere_requirement")
        ),
        "skills_required": normalize_list(skills),
        "responsibilities": normalize_list(responsibilities),
    }

    return {
        "pair_id": pair_id,
        "candidate_id": candidate_id,
        "source_dataset": "resume_data_for_ranking",
        "raw": raw,
        "normalized": normalized,
        "reference_score": reference_score,
        "reference_score_note": (
            "Dataset-provided score. Not treated as ground-truth "
            "for the explainable matching system."
        ),
    }


def write_jsonl(path, records):
    with path.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


def validate_candidate(record):
    assert record["candidate_id"]
    assert record["source_record_id"]
    assert "raw" in record
    assert "normalized" in record
    assert isinstance(record["normalized"]["skills"], list)


def validate_job(record):
    assert record["job_id"]
    assert "raw" in record
    assert "normalized" in record
    assert isinstance(record["normalized"]["skills"], list)


def validate_pair(record):
    assert record["pair_id"]
    assert record["candidate_id"]
    assert "reference_score" in record
    assert "normalized" in record


def main():
    parser = argparse.ArgumentParser(
        description="Preprocess resume and job datasets."
    )

    parser.add_argument(
        "--full",
        action="store_true",
        help="Process the complete datasets.",
    )

    parser.add_argument(
        "--sample-size",
        type=int,
        default=25,
        help="Number of rows to process in sample mode.",
    )

    args = parser.parse_args()

    INTERIM_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    if not RESUME_FILE.exists():
        raise FileNotFoundError(f"Resume dataset not found: {RESUME_FILE}")

    if not JOB_FILE.exists():
        raise FileNotFoundError(f"Job dataset not found: {JOB_FILE}")

    print("=" * 70)
    print("STEP 12.2 - DATASET PREPROCESSING")
    print("=" * 70)

    print(f"Resume file: {RESUME_FILE}")
    print(f"Job file:    {JOB_FILE}")

    print("\nLoading datasets...")

    resume_df = pd.read_csv(RESUME_FILE)
    job_df = pd.read_csv(JOB_FILE)

    print(f"Resume rows available: {len(resume_df)}")
    print(f"Job rows available:    {len(job_df)}")

    if args.full:
        resume_work = resume_df
        job_work = job_df
        mode = "full"
    else:
        sample_size = min(args.sample_size, len(resume_df), len(job_df))
        resume_work = resume_df.head(sample_size)
        job_work = job_df.head(sample_size)
        mode = f"sample_{sample_size}"

    print(f"\nProcessing mode: {mode}")

    candidates = []
    pairs = []

    for index, (_, row) in enumerate(resume_work.iterrows(), start=1):
        candidate = build_candidate(row, index)
        pair = build_resume_job_pair(row, index)

        validate_candidate(candidate)
        validate_pair(pair)

        candidates.append(candidate)
        pairs.append(pair)

    jobs = []

    for index, (_, row) in enumerate(job_work.iterrows(), start=1):
        job = build_job(row, index)

        validate_job(job)
        jobs.append(job)

    if args.full:
        candidate_path = PROCESSED_DIR / "candidates.jsonl"
        job_path = PROCESSED_DIR / "jobs.jsonl"
        pair_path = PROCESSED_DIR / "resume_job_pairs.jsonl"
        metadata_path = PROCESSED_DIR / "processing_metadata.json"
    else:
        candidate_path = INTERIM_DIR / "sample_candidates.jsonl"
        job_path = INTERIM_DIR / "sample_jobs.jsonl"
        pair_path = INTERIM_DIR / "sample_resume_job_pairs.jsonl"
        metadata_path = INTERIM_DIR / "sample_processing_metadata.json"

    write_jsonl(candidate_path, candidates)
    write_jsonl(job_path, jobs)
    write_jsonl(pair_path, pairs)

    metadata = {
        "schema_version": SCHEMA_VERSION,
        "processed_at_utc": datetime.now(timezone.utc).isoformat(),
        "mode": mode,
        "sources": {
            "resume_dataset": str(RESUME_FILE.relative_to(ROOT)),
            "job_dataset": str(JOB_FILE.relative_to(ROOT)),
        },
        "available_rows": {
            "resume_dataset": len(resume_df),
            "job_dataset": len(job_df),
        },
        "processed_rows": {
            "candidates": len(candidates),
            "jobs": len(jobs),
            "resume_job_pairs": len(pairs),
        },
        "outputs": [
            str(candidate_path.relative_to(ROOT)),
            str(job_path.relative_to(ROOT)),
            str(pair_path.relative_to(ROOT)),
        ],
        "important_notes": [
            "Raw datasets are never modified.",
            "Normalized fields are lowercase and whitespace-normalized.",
            "Original source text is preserved under raw fields.",
            "Skill aliases are not merged during preprocessing.",
            "Relationships such as ADJACENT or TRANSFERABLE are handled later.",
            "Dataset matched_score is retained only as a reference field.",
            "Missing values are not interpreted as negative evidence.",
        ],
    }

    with metadata_path.open("w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 70)
    print("PREPROCESSING COMPLETE")
    print("=" * 70)

    print(f"Candidates:        {len(candidates)}")
    print(f"Jobs:              {len(jobs)}")
    print(f"Resume-job pairs:  {len(pairs)}")

    print("\nOutput files:")
    print(f"  {candidate_path}")
    print(f"  {job_path}")
    print(f"  {pair_path}")
    print(f"  {metadata_path}")

    print("\nValidation examples:")

    if candidates:
        c = candidates[0]
        print("\nFirst candidate:")
        print(f"  ID: {c['candidate_id']}")
        print(f"  Skills: {c['normalized']['skills'][:10]}")
        print(
            "  Responsibilities:",
            c["normalized"]["responsibilities"][:5],
        )

    if jobs:
        j = jobs[0]
        print("\nFirst job:")
        print(f"  ID: {j['job_id']}")
        print(f"  Title: {j['normalized']['title']}")
        print(f"  Skills: {j['normalized']['skills'][:10]}")

    if pairs:
        p = pairs[0]
        print("\nFirst resume-job pair:")
        print(f"  Pair ID: {p['pair_id']}")
        print(f"  Candidate: {p['candidate_id']}")
        print(f"  Job title: {p['normalized']['job_title']}")
        print(
            f"  Required skills: "
            f"{p['normalized']['skills_required'][:10]}"
        )
        print(f"  Reference score: {p['reference_score']}")

    print("\nDONE.")


if __name__ == "__main__":
    main()