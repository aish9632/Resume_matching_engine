from typing import Dict, List


def _format_match(item: Dict) -> Dict:
    return {
        "requirement": item.get("requirement"),
        "relationship": item.get("relationship"),
        "score": item.get("final_requirement_score"),
        "evidence_ids": item.get("evidence_ids", []),
        "explanation": item.get("explanation"),
    }


def generate_explanation(match_result: Dict) -> Dict:

    requirement_analysis = match_result.get(
        "requirement_analysis",
        [],
    )

    strong_matches: List[Dict] = []
    partial_matches: List[Dict] = []
    missing_requirements: List[Dict] = []

    for item in requirement_analysis:

        relationship = item.get("relationship")

        if relationship == "EXACT":
            strong_matches.append(
                _format_match(item)
            )

        elif relationship in {
            "CAPABILITY",
            "RELATED",
            "TRANSFERABLE",
            "ADJACENT",
            "PARTIAL",
        }:
            partial_matches.append(
                _format_match(item)
            )

        elif relationship == "MISSING":
            missing_requirements.append(
                _format_match(item)
            )

    critical_gaps = [
        _format_match(item)
        for item in match_result.get(
            "critical_gaps",
            [],
        )
    ]

    decision_score = float(
        match_result.get("fit_score", 0)
    )

    raw_score = float(
        match_result.get(
            "fit_score_before_guardrails",
            decision_score,
        )
    )

    coverage = float(
        match_result.get(
            "evidence_coverage",
            0,
        )
    )

    confidence = float(
        match_result.get(
            "confidence",
            0,
        )
    )

    recommendation = match_result.get(
        "recommendation",
        "UNKNOWN",
    )

    summary = (
        f"The candidate has a raw requirement fit of "
        f"{raw_score:.2f}/100 and a decision-adjusted fit "
        f"of {decision_score:.2f}/100, with evidence coverage "
        f"of {coverage:.0%} and confidence of {confidence:.0%}. "
    )

    if critical_gaps:
        summary += (
            f"There are {len(critical_gaps)} critical must-have "
            "requirement gap(s). Therefore, the system does not "
            "recommend the candidate despite other supported matches."
        )

    elif strong_matches and not missing_requirements:
        summary += (
            "The candidate directly satisfies the evaluated "
            "requirements with supporting resume evidence."
        )

    elif partial_matches:
        summary += (
            "The candidate has relevant or transferable evidence, "
            "but some requirements are only partially supported."
        )

    else:
        summary += (
            "The available resume evidence provides limited "
            "support for the job requirements."
        )

    return {
        "summary": summary,
        "raw_fit_score": round(raw_score, 2),
        "decision_fit_score": round(decision_score, 2),
        "confidence": round(confidence, 4),
        "evidence_coverage": coverage,
        "recommendation": recommendation,
        "strong_matches": strong_matches,
        "partial_matches": partial_matches,
        "missing_requirements": missing_requirements,
        "critical_gaps": critical_gaps,
    }