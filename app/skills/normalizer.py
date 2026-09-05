import re

from app.skills.taxonomy import SKILL_ALIASES


def clean_skill(skill: str) -> str:
    if not skill:
        return ""

    skill = str(skill).strip().lower()
    skill = re.sub(r"\s+", " ", skill)

    return skill.strip(" .,;:-")


def normalize_skill(skill: str) -> str:
    skill = clean_skill(skill)

    if not skill:
        return ""

    return SKILL_ALIASES.get(skill, skill)


def normalize_skills(skills):
    if not isinstance(skills, list):
        return []

    normalized = []

    for skill in skills:
        value = normalize_skill(skill)

        if value and value not in normalized:
            normalized.append(value)

    return normalized
