from app.matching.requirement_matcher import match_requirement


def evidence(concept, text=None, strength=4):
    return {
        "evidence_id": f"E_{concept.replace(' ', '_')}",
        "text": text or concept,
        "canonical_concepts": [concept],
        "evidence_strength": strength,
    }


def requirement(concept, importance="IMPORTANT"):
    return {
        "requirement_id": f"R_{concept.replace(' ', '_')}",
        "requirement": f"Experience with {concept}",
        "text": f"Experience with {concept}",
        "canonical_concept": concept,
        "type": "SKILL",
        "importance": importance,
        "minimum_experience": None,
    }


def test_exact_skill_match():
    result = match_requirement(requirement("react"), [evidence("react")])
    assert result["relationship"] == "EXACT"
    assert result["evidence_ids"]


def test_alias_match():
    result = match_requirement(requirement("react"), [evidence("react.js")])
    assert result["relationship"] == "EXACT"


def test_capability_match():
    result = match_requirement(requirement("frontend development"), [evidence("react")])
    assert result["relationship"] == "CAPABILITY"


def test_related_skill_not_exact():
    result = match_requirement(requirement("react"), [evidence("redux")])
    assert result["relationship"] == "RELATED"
    assert result["relationship"] != "EXACT"


def test_adjacent_skill_not_exact():
    result = match_requirement(requirement("react"), [evidence("angular")])
    assert result["relationship"] == "ADJACENT"
    assert result["relationship"] != "EXACT"


def test_unrelated_skill_is_missing():
    result = match_requirement(requirement("kubernetes"), [evidence("html")])
    assert result["relationship"] == "MISSING"
    assert result["evidence_ids"] == []


def test_evidence_is_required_for_match():
    result = match_requirement(requirement("react"), [])
    assert result["relationship"] == "MISSING"
    assert result["evidence_ids"] == []


def test_negated_evidence_does_not_match():
    result = match_requirement(
        requirement("kubernetes"),
        [{
            "evidence_id": "E_NEGATED",
            "text": "No experience with Kubernetes",
            "canonical_concepts": ["kubernetes"],
            "evidence_strength": 0,
            "polarity": "NEGATED",
            "status": "NEGATED",
        }]
    )
    assert result["relationship"] == "MISSING"
    assert result["evidence_ids"] == []


def test_learning_status_does_not_equal_demonstrated_experience():
    result = match_requirement(
        requirement("kubernetes"),
        [{
            "evidence_id": "E_LEARNING",
            "text": "Currently learning Kubernetes",
            "canonical_concepts": ["kubernetes"],
            "evidence_strength": 1,
            "polarity": "POSITIVE",
            "status": "LEARNING",
        }]
    )
    assert result["relationship"] == "EXACT"
    assert result["evidence_ids"]
    assert result["evidence_strength"] == 1


def test_keyword_stuffing_does_not_create_unrelated_match():
    result = match_requirement(
        requirement("kubernetes"),
        [evidence("html", "HTML HTML HTML HTML HTML HTML", strength=5)]
    )
    assert result["relationship"] == "MISSING"
    assert result["evidence_ids"] == []
