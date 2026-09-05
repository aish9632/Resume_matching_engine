def calculate_confidence(match_result: dict) -> float:
    coverage = float(
        match_result.get("evidence_coverage", 0.0)
    )

    requirement_results = match_result.get(
        "requirement_analysis",
        [],
    )

    if not requirement_results:
        return 0.0

    # Average semantic/relationship quality of the analyzed requirements.
    match_quality = sum(
        float(item.get("semantic_score", 0.0))
        for item in requirement_results
    ) / len(requirement_results)

    # Average strength of the supporting evidence.
    evidence_strength = sum(
        min(
            1.0,
            float(item.get("evidence_strength", 0.0)) / 5.0,
        )
        for item in requirement_results
        if item.get("evidence_ids")
    )

    supported_items = sum(
        1
        for item in requirement_results
        if item.get("evidence_ids")
    )

    if supported_items:
        evidence_strength /= supported_items
    else:
        evidence_strength = 0.0

    # Critical gaps reduce confidence in the assessment.
    critical_gaps = match_result.get("critical_gaps", [])
    critical_gap_factor = 1.0

    if critical_gaps:
        critical_gap_factor = max(
            0.50,
            1.0 - 0.15 * len(critical_gaps),
        )

    confidence = (
        0.40 * coverage
        + 0.30 * match_quality
        + 0.30 * evidence_strength
    )

    confidence *= critical_gap_factor

    return round(
        max(0.0, min(1.0, confidence)),
        4,
    )