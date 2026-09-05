from typing import Dict


def generate_recommendation(match_result: Dict) -> str:
    score = float(match_result["fit_score"])
    critical_gaps = match_result.get("critical_gaps", [])
    coverage = float(match_result.get("evidence_coverage", 0.0))

    if critical_gaps:
        return "NOT_RECOMMENDED"

    if coverage < 0.30:
        return "INSUFFICIENT_EVIDENCE"

    if score >= 75:
        return "STRONG_MATCH"

    if score >= 60:
        return "GOOD_MATCH"

    if score >= 45:
        return "POTENTIAL_MATCH"

    return "LOW_MATCH"


def recommendation_reason(
    match_result: Dict,
    recommendation: str,
) -> str:

    if recommendation == "STRONG_MATCH":
        return (
            "The candidate satisfies most important requirements with "
            "strong supporting evidence and has no critical must-have gaps."
        )

    if recommendation == "GOOD_MATCH":
        return (
            "The candidate satisfies a substantial portion of the job "
            "requirements with supporting evidence."
        )

    if recommendation == "POTENTIAL_MATCH":
        return (
            "The candidate has relevant or transferable evidence, but "
            "some requirements are only partially supported."
        )

    if recommendation == "INSUFFICIENT_EVIDENCE":
        return (
            "The available resume evidence is insufficient to make a "
            "reliable matching assessment."
        )

    if recommendation == "NOT_RECOMMENDED":
        return (
            "One or more must-have requirements are missing from the "
            "available candidate evidence."
        )

    return (
        "The candidate has limited evidence supporting the job "
        "requirements."
    )
