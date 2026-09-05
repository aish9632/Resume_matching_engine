from typing import Dict, List

from app.matching.requirement_matcher import match_requirement


IMPORTANCE_WEIGHTS = {
    "MUST_HAVE": 1.50,
    "IMPORTANT": 1.00,
    "PREFERRED": 0.60,
    "CONTEXTUAL": 0.30,
}


def match_candidate_to_job(
    candidate_id: str,
    job_id: str,
    requirements: List[Dict],
    evidence_items: List[Dict],
) -> Dict:

    requirement_results = []

    for requirement in requirements:
        result = match_requirement(
            requirement,
            evidence_items,
        )

        importance = requirement.get(
            "importance",
            "IMPORTANT",
        )

        result["importance"] = importance
        result["importance_weight"] = IMPORTANCE_WEIGHTS.get(
            importance,
            1.0,
        )

        requirement_results.append(result)

    weighted_total = 0.0
    weight_total = 0.0

    strong_matches = []
    partial_matches = []
    missing_requirements = []
    critical_gaps = []

    for result in requirement_results:

        score = result["final_requirement_score"]
        weight = result["importance_weight"]

        weighted_total += score * weight
        weight_total += weight

        relationship = result["relationship"]

        if relationship == "EXACT":
            strong_matches.append(result)

        elif relationship in {
            "CAPABILITY",
            "RELATED",
            "TRANSFERABLE",
            "ADJACENT",
            "PARTIAL",
        }:
            partial_matches.append(result)

        elif relationship == "MISSING":
            missing_requirements.append(result)

            if result["importance"] == "MUST_HAVE":
                critical_gaps.append(result)

    overall_score = (
        weighted_total / weight_total
        if weight_total
        else 0.0
    )

    evidence_coverage = (
        len(
            [
                r for r in requirement_results
                if r["relationship"] != "MISSING"
            ]
        )
        / len(requirement_results)
        if requirement_results
        else 0.0
    )

    return {
        "match_id": f"{candidate_id}_{job_id}",
        "candidate_id": candidate_id,
        "job_id": job_id,
        "fit_score": round(overall_score * 100, 2),
        "evidence_coverage": round(evidence_coverage, 4),
        "strong_matches": strong_matches,
        "partial_matches": partial_matches,
        "missing_requirements": missing_requirements,
        "critical_gaps": critical_gaps,
        "requirement_analysis": requirement_results,
        "requirement_count": len(requirement_results),
    }
