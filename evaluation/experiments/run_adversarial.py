import json
from pathlib import Path

from app.matching.requirement_matcher import match_requirement


BASE_DIR = Path(__file__).resolve().parents[2]
CASES_FILE = BASE_DIR / "evaluation" / "experiments" / "adversarial_cases.json"


def make_requirement(concept):
    return {
        "requirement_id": f"R_{concept.replace(' ', '_')}",
        "requirement": f"Experience with {concept}",
        "text": f"Experience with {concept}",
        "canonical_concept": concept,
        "type": "SKILL",
        "importance": "IMPORTANT",
        "minimum_experience": None,
    }


def make_evidence(case):
    return {
        "evidence_id": f"E_{case['case_id']}",
        "text": case.get("candidate_text", case["candidate_skill"]),
        "canonical_concepts": [case["candidate_skill"]],
        "evidence_strength": 1 if case["type"] == "learning" else 4,
        "polarity": "NEGATED" if case["type"] == "negation" else "POSITIVE",
        "status": "NEGATED" if case["type"] == "negation" else (
            "LEARNING" if case["type"] == "learning" else "DEMONSTRATED"
        ),
    }


def main():
    cases = json.loads(CASES_FILE.read_text(encoding="utf-8-sig"))

    passed = 0

    print("\nADVERSARIAL EVALUATION")
    print("=" * 70)

    for case in cases:
        result = match_requirement(
            make_requirement(case["job_requirement"]),
            [make_evidence(case)],
        )

        actual = result["relationship"]
        expected = case["expected"]
        status = "PASS" if actual == expected else "FAIL"

        if status == "PASS":
            passed += 1

        print(
            f"{case['case_id']} | "
            f"{case['type']:16} | "
            f"Expected={expected:10} | "
            f"Actual={actual:10} | "
            f"{status}"
        )

    print("=" * 70)
    print(f"RESULT: {passed}/{len(cases)} passed")

    if passed != len(cases):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
