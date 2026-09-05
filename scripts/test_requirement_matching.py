from app.matching.requirement_matcher import match_requirement


def requirement(skill):
    return {
        "requirement_id": "TEST_REQ",
        "text": f"Experience with {skill}",
        "canonical_concept": skill,
    }


tests = [
    (
        "React",
        "angular",
        "ADJACENT",
    ),
    (
        "React",
        "redux",
        "RELATED",
    ),
    (
        "React",
        "react",
        "EXACT",
    ),
    (
        "Kubernetes",
        "html",
        "MISSING",
    ),
]


print("=" * 70)
print("STEP 16.2 - ADVERSARIAL REQUIREMENT MATCHING TEST")
print("=" * 70)

for target, candidate, expected in tests:

    evidence = [
        {
            "evidence_id": "E_TEST",
            "canonical_skill": candidate,
            "evidence_strength": 4,
            "text": f"Worked with {candidate}",
        }
    ]

    result = match_requirement(
        requirement(target),
        evidence,
    )

    actual = result["relationship"]

    print(
        f"{target} <- {candidate} | "
        f"Expected={expected} | Actual={actual} | "
        f"Score={result['final_requirement_score']}"
    )

    assert actual == expected, (
        f"Expected {expected}, got {actual}"
    )


print()
print("PASS: Adversarial requirement matching tests passed.")
