import json
import re
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.matching.requirement_matcher import match_requirement


BASE_DIR = Path(__file__).resolve().parents[2]
CASES_FILE = BASE_DIR / "evaluation" / "experiments" / "adversarial_cases.json"


def normalize(text):
    return re.sub(r"[^a-z0-9\s]", " ", text.lower()).split()


def keyword_baseline(candidate_text, requirement_text):
    candidate_words = set(normalize(candidate_text))
    requirement_words = set(normalize(requirement_text))

    if not requirement_words:
        return 0.0

    return len(candidate_words & requirement_words) / len(requirement_words)


def tfidf_baseline(candidate_text, requirement_text):
    vectorizer = TfidfVectorizer()
    matrix = vectorizer.fit_transform(
        [candidate_text, requirement_text]
    )
    return float(cosine_similarity(matrix[0:1], matrix[1:2])[0][0])


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
        "status": (
            "NEGATED"
            if case["type"] == "negation"
            else "LEARNING"
            if case["type"] == "learning"
            else "DEMONSTRATED"
        ),
    }


def main():
    cases = json.loads(
        CASES_FILE.read_text(encoding="utf-8-sig")
    )

    keyword_correct = 0
    tfidf_correct = 0
    hybrid_correct = 0

    print("\nBASELINE COMPARISON")
    print("=" * 90)

    for case in cases:
        candidate_text = case.get(
            "candidate_text",
            case["candidate_skill"],
        )
        requirement_text = case["job_requirement"]

        keyword_score = keyword_baseline(
            candidate_text,
            requirement_text,
        )

        tfidf_score = tfidf_baseline(
            candidate_text,
            requirement_text,
        )

        hybrid_result = match_requirement(
            make_requirement(case["job_requirement"]),
            [make_evidence(case)],
        )

        hybrid_relationship = hybrid_result["relationship"]
        expected = case["expected"]

        # Baselines use a conservative threshold:
        # any positive lexical/semantic similarity = MATCH.
        keyword_prediction = (
            "EXACT"
            if keyword_score > 0
            else "MISSING"
        )

        tfidf_prediction = (
            "EXACT"
            if tfidf_score >= 0.30
            else "MISSING"
        )

        if keyword_prediction == expected:
            keyword_correct += 1

        if tfidf_prediction == expected:
            tfidf_correct += 1

        if hybrid_relationship == expected:
            hybrid_correct += 1

        print(
            f"{case['case_id']} | "
            f"Keyword={keyword_prediction:7} "
            f"({keyword_score:.2f}) | "
            f"TF-IDF={tfidf_prediction:7} "
            f"({tfidf_score:.2f}) | "
            f"Hybrid={hybrid_relationship:10} | "
            f"Expected={expected}"
        )

    total = len(cases)

    print("=" * 90)
    print(f"Keyword accuracy : {keyword_correct}/{total} = {keyword_correct/total:.1%}")
    print(f"TF-IDF accuracy  : {tfidf_correct}/{total} = {tfidf_correct/total:.1%}")
    print(f"Hybrid accuracy  : {hybrid_correct}/{total} = {hybrid_correct/total:.1%}")


if __name__ == "__main__":
    main()
