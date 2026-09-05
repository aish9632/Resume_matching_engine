import re
from typing import Dict, List


ACTION_PATTERNS = {
    "BUILT": r"\b(built|build|developed|created|implemented)\b",
    "DESIGNED": r"\b(designed|architected)\b",
    "DEPLOYED": r"\b(deployed|deployment|released)\b",
    "OPTIMIZED": r"\b(optimized|improved|enhanced|tuned)\b",
    "INTEGRATED": r"\b(integrated|connected|implemented)\b",
    "MAINTAINED": r"\b(maintained|supported|managed)\b",
    "TESTED": r"\b(tested|testing|validated)\b",
    "LED": r"\b(led|lead|managed|mentored)\b",
    "CONFIGURED": r"\b(configured|setup|set up)\b",
}

NEGATION_PATTERNS = [
    r"\bno experience\b",
    r"\bnot experienced\b",
    r"\bwithout experience\b",
    r"\bnever used\b",
    r"\bhave not used\b",
    r"\bdo not have\b",
    r"\bdon't have\b",
    r"\bno knowledge\b",
]

LEARNING_PATTERNS = [
    r"\blearning\b",
    r"\blearned\b",
    r"\bcurrently learning\b",
    r"\bstudying\b",
    r"\bfamiliarizing\b",
    r"\bin progress\b",
]


def clean_sentence(text: str) -> str:
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def split_into_evidence_units(text: str) -> List[str]:
    if not text:
        return []

    text = text.replace("\r\n", "\n").replace("\r", "\n")

    units = re.split(
        r"\n+|(?<=[.!?])\s+|(?<=;)\s+",
        text,
    )

    return [
        clean_sentence(unit)
        for unit in units
        if clean_sentence(unit)
    ]


def detect_action(text: str) -> str:
    lower = text.lower()

    for action, pattern in ACTION_PATTERNS.items():
        if re.search(pattern, lower):
            return action

    return "MENTIONED"


def detect_polarity(text: str) -> str:
    lower = text.lower()

    for pattern in NEGATION_PATTERNS:
        if re.search(pattern, lower):
            return "NEGATIVE"

    return "POSITIVE"


def detect_status(text: str) -> str:
    lower = text.lower()

    for pattern in NEGATION_PATTERNS:
        if re.search(pattern, lower):
            return "NEGATED"

    for pattern in LEARNING_PATTERNS:
        if re.search(pattern, lower):
            return "LEARNING"

    action = detect_action(text)

    if action != "MENTIONED":
        return "DEMONSTRATED"

    return "MENTIONED"


def infer_source_type(section: str) -> str:
    section = section.lower()

    if section in {"experience", "work_experience", "employment"}:
        return "EXPERIENCE"

    if section in {"project", "projects"}:
        return "PROJECT"

    if section in {"skills", "technical_skills"}:
        return "SKILLS"

    if section in {"certification", "certifications"}:
        return "CERTIFICATION"

    if section in {"education"}:
        return "EDUCATION"

    return "OTHER"


def evidence_strength(source_type: str, action: str, status: str) -> int:
    if status == "NEGATED":
        return 0

    base_scores = {
        "SKILLS": 1,
        "OTHER": 1,
        "EDUCATION": 2,
        "CERTIFICATION": 2,
        "PROJECT": 3,
        "EXPERIENCE": 4,
    }

    score = base_scores.get(source_type, 1)

    if action in {
        "BUILT",
        "DESIGNED",
        "DEPLOYED",
        "OPTIMIZED",
        "INTEGRATED",
        "MAINTAINED",
        "TESTED",
        "LED",
        "CONFIGURED",
    }:
        score += 1

    return min(score, 5)


def extract_evidence_from_candidate(candidate: Dict) -> List[Dict]:
    evidence = []

    candidate_id = candidate["candidate_id"]
    normalized = candidate["normalized"]

    evidence_counter = 1

    section_sources = [
        ("skills", normalized.get("skills", []), "skills"),
        (
            "responsibilities",
            normalized.get("responsibilities", []),
            "experience",
        ),
        (
            "positions",
            normalized.get("positions", []),
            "experience",
        ),
        (
            "role_positions",
            normalized.get("role_positions", []),
            "experience",
        ),
        (
            "certifications",
            normalized.get("certifications", []),
            "certifications",
        ),
    ]

    for field, values, section in section_sources:
        source_type = infer_source_type(section)

        for value in values:
            if not value:
                continue

            action = detect_action(value)
            polarity = detect_polarity(value)
            status = detect_status(value)

            evidence.append(
                {
                    "evidence_id": (
                        f"E_{candidate_id}_{evidence_counter:04d}"
                    ),
                    "candidate_id": candidate_id,
                    "text": value,
                    "section": section,
                    "page": None,
                    "canonical_concepts": [value],
                    "action": action,
                    "polarity": polarity,
                    "status": status,
                    "source_type": source_type,
                    "evidence_strength": evidence_strength(
                        source_type,
                        action,
                        status,
                    ),
                    "extraction_confidence": 0.85,
                }
            )

            evidence_counter += 1

    return evidence


def extract_textual_evidence(candidate: Dict) -> List[Dict]:
    """
    Extract contextual evidence from the original resume fields.
    """
    evidence = []

    candidate_id = candidate["candidate_id"]
    raw = candidate["raw"]

    sections = [
        ("career_objective", raw.get("career_objective", "")),
        ("responsibilities", raw.get("responsibilities", "")),
    ]

    counter = 1000

    for section, text in sections:
        units = split_into_evidence_units(text)

        for unit in units:
            if len(unit) < 5:
                continue

            action = detect_action(unit)
            polarity = detect_polarity(unit)
            status = detect_status(unit)
            source_type = infer_source_type(section)

            evidence.append(
                {
                    "evidence_id": (
                        f"E_{candidate_id}_{counter:04d}"
                    ),
                    "candidate_id": candidate_id,
                    "text": unit,
                    "section": section,
                    "page": None,
                    "canonical_concepts": [],
                    "action": action,
                    "polarity": polarity,
                    "status": status,
                    "source_type": source_type,
                    "evidence_strength": evidence_strength(
                        source_type,
                        action,
                        status,
                    ),
                    "extraction_confidence": 0.80,
                }
            )

            counter += 1

    return evidence


def extract_candidate_evidence(candidate: Dict) -> List[Dict]:
    structured = extract_evidence_from_candidate(candidate)
    textual = extract_textual_evidence(candidate)

    return structured + textual