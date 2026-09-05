from app.skills.relationship_engine import classify_relationship
from app.skills.relationship_engine import semantic_similarity


RELATIONSHIP_SCORES = {
    "EXACT": 1.00,
    "CAPABILITY": 0.85,
    "SEMANTIC": 0.78,
    "RELATED": 0.72,
    "TRANSFERABLE": 0.55,
    "ADJACENT": 0.45,
    "PARTIAL": 0.30,
    "UNRELATED": 0.00,
}

def match_experience_requirement(requirement, evidence_items):
    """
    Match an explicitly stated experience-duration requirement.

    Experience is only considered when the candidate evidence
    contains an explicit numeric duration. We never infer years
    from job titles, dates, or vague phrases such as
    'robust experience'.
    """
    required_years = requirement.get("minimum_experience")

    if required_years is None:
        return None

    best_evidence = None

    for evidence in evidence_items:
        if (
            evidence.get("polarity") == "NEGATED"
            or evidence.get("status") == "NEGATED"
        ):
            continue

        candidate_years = evidence.get("experience_years")

        if candidate_years is None:
            continue

        if (
            best_evidence is None
            or candidate_years > best_evidence["experience_years"]
        ):
            best_evidence = {
                "evidence": evidence,
                "experience_years": candidate_years,
            }

    if best_evidence is None:
        return None

    evidence = best_evidence["evidence"]
    candidate_years = best_evidence["experience_years"]

    experience_score = min(
        candidate_years / required_years,
        1.0,
    )

    return {
        "relationship": (
            "EXACT"
            if candidate_years >= required_years
            else "PARTIAL"
        ),
        "semantic_score": experience_score,
        "evidence_strength": evidence.get(
            "evidence_strength",
            0,
        ),
        "coverage": experience_score,
        "final_requirement_score": experience_score,
        "evidence": evidence,
        "candidate_years": candidate_years,
        "required_years": required_years,
    }

def classify_evidence_semantically(evidence_text, requirement_text):
    """
    Use embedding similarity as supporting evidence.

    Important:
    - Semantic similarity is never treated as EXACT.
    - Embeddings cannot invent evidence.
    - The candidate must already have an evidence item.
    """

    if not evidence_text or not requirement_text:
        return None

    similarity = semantic_similarity(
        evidence_text,
        requirement_text,
    )

    if similarity >= 0.82:
        return {
            "relationship": "SEMANTIC",
            "semantic_score": similarity,
            "confidence": min(0.90, similarity),
        }

    if similarity >= 0.68:
        return {
            "relationship": "ADJACENT",
            "semantic_score": similarity,
            "confidence": similarity,
        }

    return None


def match_requirement(requirement, evidence_items):
    """
    Match one job requirement against candidate evidence.

    Matching has two complementary paths:

    1. Structured concept relationship:
       exact, capability, related, transferable, adjacent.

    2. Evidence-text semantic support:
       compares the actual candidate evidence sentence with
       the actual requirement text.

    Structured relationships are preferred because they are
    more interpretable. Semantic similarity is supporting
    evidence and is never treated as exact.
    """

    target = requirement["canonical_concept"]
    requirement_text = requirement.get(
        "text",
        target,
    )

    best_match = None
    
    experience_match = match_experience_requirement(
        requirement,
        evidence_items,
    )

    if experience_match is not None:
        evidence = experience_match["evidence"]

        if experience_match["relationship"] == "EXACT":
            explanation = (
                f"Candidate explicitly states "
                f"{experience_match['candidate_years']:.1f} years "
                f"of experience, meeting the required "
                f"{experience_match['required_years']:.1f} years: "
                f"'{evidence['text']}'."
            )
        else:
            explanation = (
                f"Candidate explicitly states "
                f"{experience_match['candidate_years']:.1f} years "
                f"of experience, below the required "
                f"{experience_match['required_years']:.1f} years: "
                f"'{evidence['text']}'."
            )

        return {
            "requirement_id": requirement["requirement_id"],
            "requirement": requirement["text"],
            "canonical_concept": target,
            "relationship": experience_match["relationship"],
            "semantic_score": experience_match["semantic_score"],
            "evidence_strength": experience_match["evidence_strength"],
            "coverage": experience_match["coverage"],
            "final_requirement_score": experience_match[
                "final_requirement_score"
            ],
            "evidence_ids": [
                evidence["evidence_id"]
            ],
            "explanation": explanation,
        }

    for evidence in evidence_items:

        concepts = evidence.get(
            "canonical_concepts"
        )

        # Backward compatibility with the original
        # evidence contract used by existing tests.
        if concepts is None:
            canonical_skill = evidence.get(
                "canonical_skill"
            )

            if canonical_skill:
                concepts = [canonical_skill]
            else:
                concepts = []

        if isinstance(concepts, str):
            concepts = [concepts]

        if (
            evidence.get("polarity") == "NEGATED"
            or evidence.get("status") == "NEGATED"
        ):
            continue

        evidence_strength = evidence.get(
            "evidence_strength",
            0,
        )

        evidence_score = min(
            1.0,
            evidence_strength / 5.0,
        )

        # -----------------------------------------------------
        # PATH 1 — structured concept relationships
        # -----------------------------------------------------

        for candidate_skill in concepts:

            relationship_result = classify_relationship(
                candidate_skill,
                target,
            )

            relationship = relationship_result[
                "relationship"
            ]

            if relationship == "UNRELATED":
                continue

            relationship_score = RELATIONSHIP_SCORES.get(
                relationship,
                0.0,
            )

            combined_score = (
                0.65 * relationship_score
                + 0.35 * evidence_score
            )

            if (
                best_match is None
                or combined_score
                > best_match["combined_score"]
            ):
                best_match = {
                    "candidate_skill": candidate_skill,
                    "relationship": relationship,
                    "relationship_score": relationship_score,
                    "semantic_score": relationship_result.get(
                        "semantic_score",
                        relationship_score,
                    ),
                    "evidence_strength": evidence_strength,
                    "evidence_score": evidence_score,
                    "combined_score": combined_score,
                    "evidence": evidence,
                    "match_path": "structured",
                }

        # -----------------------------------------------------
        # PATH 2 — evidence text semantic matching
        # -----------------------------------------------------

        semantic_result = classify_evidence_semantically(
            evidence.get("text", ""),
            requirement_text,
        )

        if semantic_result:

            relationship = semantic_result[
                "relationship"
            ]

            relationship_score = RELATIONSHIP_SCORES[
                relationship
            ]

            combined_score = (
                0.65 * relationship_score
                + 0.35 * evidence_score
            )

            if (
                best_match is None
                or combined_score
                > best_match["combined_score"]
            ):
                best_match = {
                    "candidate_skill": None,
                    "relationship": relationship,
                    "relationship_score": relationship_score,
                    "semantic_score": semantic_result[
                        "semantic_score"
                    ],
                    "evidence_strength": evidence_strength,
                    "evidence_score": evidence_score,
                    "combined_score": combined_score,
                    "evidence": evidence,
                    "match_path": "semantic_evidence",
                }

    # ---------------------------------------------------------
    # No supporting evidence
    # ---------------------------------------------------------

    if best_match is None:
        return {
            "requirement_id": requirement["requirement_id"],
            "requirement": requirement["text"],
            "canonical_concept": target,
            "relationship": "MISSING",
            "semantic_score": 0.0,
            "evidence_strength": 0,
            "coverage": 0.0,
            "final_requirement_score": 0.0,
            "evidence_ids": [],
            "explanation": (
                "No supporting candidate evidence was found "
                "for this requirement."
            ),
        }

    evidence = best_match["evidence"]
    relationship = best_match["relationship"]

    # ---------------------------------------------------------
    # Explanation
    # ---------------------------------------------------------

    if relationship == "EXACT":

        explanation = (
            f"Direct evidence found for {target}: "
            f"'{evidence['text']}'."
        )

    elif relationship == "CAPABILITY":

        explanation = (
            f"Candidate evidence '{evidence['text']}' "
            f"supports the capability '{target}'. "
            f"This is treated as a capability match, "
            f"not an exact keyword match."
        )

    elif relationship == "SEMANTIC":

        explanation = (
            f"Candidate evidence '{evidence['text']}' "
            f"semantically supports the requirement "
            f"'{requirement_text}'. "
            f"This is treated as semantic supporting evidence, "
            f"not an exact match."
        )

    else:

        explanation = (
            f"Candidate evidence '{evidence['text']}' "
            f"supports {target} through a "
            f"{relationship.lower()} relationship; "
            f"it is not treated as an exact match."
        )

    return {
        "requirement_id": requirement["requirement_id"],
        "requirement": requirement["text"],
        "canonical_concept": target,
        "relationship": relationship,
        "semantic_score": best_match["semantic_score"],
        "evidence_strength": best_match["evidence_strength"],
        "coverage": best_match["combined_score"],
        "final_requirement_score": best_match["combined_score"],
        "evidence_ids": [
            evidence["evidence_id"]
        ],
        "explanation": explanation,
    }