from typing import Dict


def apply_guardrails(match_result: Dict) -> Dict:
    raw_score = float(match_result["fit_score"])
    score = raw_score

    critical_gaps = match_result.get("critical_gaps", [])
    evidence_coverage = float(
        match_result.get("evidence_coverage", 0.0)
    )

    penalties = []

    # Critical must-have gaps materially reduce the decision score.
    if critical_gaps:
        penalty = min(25.0, 10.0 * len(critical_gaps))
        score -= penalty

        penalties.append({
            "type": "CRITICAL_GAP",
            "count": len(critical_gaps),
            "penalty": penalty,
            "reason": (
                "Missing must-have requirements reduce the "
                "decision-adjusted fit score."
            ),
        })

    # Low evidence coverage reduces confidence in the assessment.
    if evidence_coverage < 0.30:
        penalty = 10.0
        score -= penalty

        penalties.append({
            "type": "LOW_EVIDENCE_COVERAGE",
            "penalty": penalty,
            "reason": (
                "Too few requirements have supporting candidate evidence."
            ),
        })

    score = max(0.0, min(100.0, score))

    return {
        **match_result,
        "fit_score_before_guardrails": round(raw_score, 2),
        "fit_score": round(score, 2),
        "guardrail_penalties": penalties,
    }