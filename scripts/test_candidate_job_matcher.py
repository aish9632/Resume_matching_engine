from app.matching.candidate_job_matcher import match_candidate_to_job


requirements = [
    {
        "requirement_id": "R1",
        "text": "Experience with React",
        "canonical_concept": "react",
        "importance": "MUST_HAVE",
    },
    {
        "requirement_id": "R2",
        "text": "Experience with Redux",
        "canonical_concept": "redux",
        "importance": "IMPORTANT",
    },
    {
        "requirement_id": "R3",
        "text": "Experience with Kubernetes",
        "canonical_concept": "kubernetes",
        "importance": "MUST_HAVE",
    },
]

evidence = [
    {
        "evidence_id": "E1",
        "canonical_skill": "react",
        "evidence_strength": 4,
        "text": "Built frontend applications using React",
    },
    {
        "evidence_id": "E2",
        "canonical_skill": "angular",
        "evidence_strength": 4,
        "text": "Built frontend applications using Angular",
    },
]

result = match_candidate_to_job(
    "C_TEST",
    "J_TEST",
    requirements,
    evidence,
)

print("=" * 70)
print("STEP 16.3 - CANDIDATE-JOB MATCHING TEST")
print("=" * 70)

print(f"Fit score: {result['fit_score']}")
print(f"Evidence coverage: {result['evidence_coverage']}")
print(f"Strong matches: {len(result['strong_matches'])}")
print(f"Partial matches: {len(result['partial_matches'])}")
print(f"Missing requirements: {len(result['missing_requirements'])}")
print(f"Critical gaps: {len(result['critical_gaps'])}")

print()

for item in result["requirement_analysis"]:
    print(
        f"{item['requirement']} | "
        f"{item['relationship']} | "
        f"{item['final_requirement_score']}"
    )

assert result["fit_score"] > 0
assert len(result["strong_matches"]) == 1
assert len(result["missing_requirements"]) == 1
assert len(result["critical_gaps"]) == 1

print()
print("PASS: Candidate-JD matching is working.")
