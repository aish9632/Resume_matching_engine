from app.skills.relationship_engine import classify_relationship


TEST_CASES = [
    ("React.js", "React", "EXACT"),
    ("ReactJS", "React", "EXACT"),
    ("Angular", "React", "ADJACENT"),
    ("Vue", "React", "ADJACENT"),
    ("Redux", "React", "RELATED"),
    ("JavaScript", "React", "RELATED"),
    ("Python", "Machine Learning", "RELATED"),
    ("TensorFlow", "PyTorch", "RELATED"),
    ("Docker", "Kubernetes", "RELATED"),
    ("AWS", "Azure", "ADJACENT"),
    ("HTML", "Kubernetes", "UNRELATED"),
    ("Excel", "React", "UNRELATED"),
]


print("=" * 70)
print("STEP 15.2 - ADVERSARIAL SKILL RELATIONSHIP TEST")
print("=" * 70)

failures = []

for candidate, target, expected in TEST_CASES:
    result = classify_relationship(candidate, target)
    actual = result["relationship"]

    status = "PASS" if actual == expected else "FAIL"

    print(
        f"{status}: "
        f"{candidate} -> {target} | "
        f"Expected={expected} | Actual={actual}"
    )

    if actual != expected:
        failures.append(
            (candidate, target, expected, actual)
        )


assert not failures, f"Relationship test failures: {failures}"

print()
print("PASS: All adversarial relationship tests passed.")
