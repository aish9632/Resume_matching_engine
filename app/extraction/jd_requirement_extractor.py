import re
from typing import Dict, List


IMPORTANCE_PATTERNS = {
    "MUST_HAVE": [
        r"\brequired\b",
        r"\bmust have\b",
        r"\bmandatory\b",
        r"\bessential\b",
        r"\bminimum requirement\b",
    ],
    "PREFERRED": [
        r"\bpreferred\b",
        r"\bnice to have\b",
        r"\bbonus\b",
        r"\bplus\b",
        r"\bdesirable\b",
    ],
}


def clean_text(text: str) -> str:
    if not text:
        return ""

    text = str(text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def normalize_concept(text: str) -> str:
    text = clean_text(text).lower()

    text = re.sub(
        r"^(experience with|experience in|knowledge of|proficiency in|"
        r"proficient in|skills in|skill in|expertise in)\s+",
        "",
        text,
    )

    return text.strip(" .,:;-")


def detect_importance(text: str) -> str:
    text_lower = clean_text(text).lower()

    for importance, patterns in IMPORTANCE_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, text_lower):
                return importance

    return "IMPORTANT"


def split_description(description: str) -> List[str]:
    description = clean_text(description)

    if not description:
        return []

    # Split common JD formatting styles.
    parts = re.split(
        r"(?:\n|•|;|\u2022|\.\s+(?=[A-Z]))",
        description,
    )

    return [
        clean_text(part)
        for part in parts
        if clean_text(part)
    ]


def detect_experience_requirements(description: str) -> List[Dict]:
    requirements = []

    pattern = re.compile(
        r"(\d+(?:\.\d+)?)\+?\s*(?:years?|yrs?)"
        r"(?:\s+of\s+(?:relevant\s+)?experience)?",
        re.IGNORECASE,
    )

    for index, match in enumerate(pattern.finditer(description), start=1):
        start = max(0, match.start() - 100)
        end = min(len(description), match.end() + 150)

        source_text = clean_text(description[start:end])

        requirements.append(
            {
                "type": "EXPERIENCE",
                "text": match.group(0),
                "canonical_concept": "professional experience",
                "importance": detect_importance(source_text),
                "minimum_experience": float(match.group(1)),
                "source_text": source_text,
                "confidence": 0.85,
            }
        )

    return requirements


def detect_education_requirements(description: str) -> List[Dict]:
    requirements = []

    # Only inspect text belonging to an education/qualification section.
    section_match = re.search(
        r"(?:education|educational requirements|academic qualifications)"
        r"\s*[:\-]?\s*(.*?)(?="
        r"\b(?:experience|work experience|qualifications|"
        r"required qualifications|preferred qualifications|"
        r"licenses|certifications|skills)\b|$)",
        description,
        flags=re.IGNORECASE | re.DOTALL,
    )

    if not section_match:
        return requirements

    education_text = section_match.group(1).strip()

    education_patterns = [
        r"\bbachelor'?s\b",
        r"\bmaster'?s\b",
        r"\bph\.?d\.?\b",
        r"\bdegree\b",
        r"\bcomputer science\b",
        r"\binformation technology\b",
        r"\bengineering\b",
    ]

    sentences = split_description(education_text)

    for sentence in sentences:
        sentence_lower = sentence.lower()

        if any(
            re.search(pattern, sentence_lower)
            for pattern in education_patterns
        ):
            requirements.append(
                {
                    "type": "EDUCATION",
                    "text": sentence,
                    "canonical_concept": "education",
                    "importance": detect_importance(sentence),
                    "minimum_experience": None,
                    "source_text": sentence,
                    "confidence": 0.90,
                }
            )

    return requirements


def extract_skill_requirements(job: Dict) -> List[Dict]:
    requirements = []

    skills = job.get("normalized", {}).get("skills", [])

    if not isinstance(skills, list):
        return requirements

    description = clean_text(
        job.get("normalized", {}).get(
            "description",
            job.get("raw", {}).get("job_description", ""),
        )
    )

    for skill in skills:
        skill = clean_text(skill)

        if not skill:
            continue

        # Find nearby JD context when possible.
        source_text = skill
        importance = "IMPORTANT"

        if description:
            match = re.search(
                re.escape(skill),
                description,
                re.IGNORECASE,
            )

            if match:
                start = max(0, match.start() - 100)
                end = min(len(description), match.end() + 150)
                source_text = clean_text(
                    description[start:end]
                )
                importance = detect_importance(source_text)

        requirements.append(
            {
                "type": "SKILL",
                "text": f"Experience with {skill}",
                "canonical_concept": normalize_concept(skill),
                "importance": importance,
                "minimum_experience": None,
                "source_text": source_text,
                "confidence": 0.95,
            }
        )

    return requirements


def extract_responsibility_requirements(description: str) -> List[Dict]:
    requirements = []

    sentences = split_description(description)

    responsibility_patterns = [
        r"\bresponsible for\b",
        r"\bresponsibilities\b",
        r"\bduties\b",
        r"\bdevelop\b",
        r"\bdesign\b",
        r"\bbuild\b",
        r"\bimplement\b",
        r"\bmaintain\b",
        r"\bmanage\b",
        r"\bdeploy\b",
        r"\banalyze\b",
        r"\blead\b",
    ]

    for sentence in sentences:
        sentence = clean_text(sentence)

        # Never create a requirement from an abnormally large JD chunk.
        # This prevents the entire job description from becoming one
        # contextual requirement.
        if len(sentence) > 500:
            continue

        sentence_lower = sentence.lower()

        if any(
            re.search(pattern, sentence_lower)
            for pattern in responsibility_patterns
        ):
            requirements.append(
                {
                    "type": "RESPONSIBILITY",
                    "text": sentence,
                    "canonical_concept": normalize_concept(sentence),
                    "importance": "CONTEXTUAL",
                    "minimum_experience": None,
                    "source_text": sentence,
                    "confidence": 0.70,
                }
            )

    return requirements


def deduplicate_requirements(
    requirements: List[Dict],
) -> List[Dict]:

    unique = []
    seen = set()

    for requirement in requirements:
        key = (
            requirement["type"],
            requirement["canonical_concept"],
            requirement["importance"],
        )

        if key in seen:
            continue

        seen.add(key)
        unique.append(requirement)

    return unique


def extract_job_requirements(job: Dict) -> List[Dict]:
    normalized = job.get("normalized", {})
    raw = job.get("raw", {})

    description = clean_text(
        normalized.get(
            "description",
            raw.get("job_description", ""),
        )
    )

    requirements = []

    # 1. Structured skills from the JD dataset.
    requirements.extend(
        extract_skill_requirements(job)
    )

    # 2. Experience requirements.
    requirements.extend(
        detect_experience_requirements(description)
    )

    # 3. Education requirements.
    requirements.extend(
        detect_education_requirements(description)
    )

    # 4. Responsibilities/context.
    requirements.extend(
        extract_responsibility_requirements(description)
    )

    requirements = deduplicate_requirements(
        requirements
    )

    final_requirements = []

    for index, requirement in enumerate(
        requirements,
        start=1,
    ):
        requirement = dict(requirement)

        requirement["requirement_id"] = (
            f"{job['job_id']}_REQ_{index:04d}"
        )

        final_requirements.append(requirement)

    return final_requirements