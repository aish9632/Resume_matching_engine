from functools import lru_cache

from sentence_transformers import SentenceTransformer


MODEL_NAME = "all-MiniLM-L6-v2"


# -------------------------------------------------------------------
# Relationship scores
# -------------------------------------------------------------------

RELATIONSHIP_SCORES = {
    "EXACT": 1.00,
    "CAPABILITY": 0.85,
    "SEMANTIC": 0.78,
    "RELATED": 0.72,
    "TRANSFERABLE": 0.55,
    "ADJACENT": 0.45,
    "UNRELATED": 0.00,
}


# -------------------------------------------------------------------
# Skill aliases
# -------------------------------------------------------------------
# These normalize different spellings of the same concept.
#
# React.js -> React
# ReactJS  -> React
# Node.js  -> Node
# -------------------------------------------------------------------

ALIASES = {
    "react.js": "react",
    "reactjs": "react",
    "react js": "react",

    "node.js": "node",
    "nodejs": "node",
    "node js": "node",

    "angular.js": "angular",

    "vue.js": "vue",

    "machine-learning": "machine learning",
    "deep-learning": "deep learning",

    "scikit-learn": "scikit learn",
    "sklearn": "scikit learn",

    "postgresql": "postgres",
    "postgres sql": "postgres",

    "mongodb database": "mongodb",

    "amazon web services": "aws",
    "microsoft azure": "azure",
    "google cloud platform": "gcp",

    "k8s": "kubernetes",
}


# -------------------------------------------------------------------
# Capability relationships
# -------------------------------------------------------------------
# Directional.
#
# Example:
# React -> Frontend Development = CAPABILITY
#
# But:
# Frontend Development -> React
# is NOT automatically true.
# -------------------------------------------------------------------

CAPABILITY_MAP = {
    # Frontend
    "react": {
        "frontend development",
        "web development",
    },

    "angular": {
        "frontend development",
        "web development",
    },

    "vue": {
        "frontend development",
        "web development",
    },

    "javascript": {
        "frontend development",
        "web development",
    },

    "typescript": {
        "frontend development",
        "web development",
    },

    "html": {
        "frontend development",
        "web development",
    },

    "css": {
        "frontend development",
        "web development",
    },

    # Backend
    "python": {
        "backend development",
        "software development",
        "data analysis",
    },

    "java": {
        "backend development",
        "software development",
    },

    "node": {
        "backend development",
        "server-side development",
    },

    "django": {
        "backend development",
        "web development",
    },

    "flask": {
        "backend development",
        "web development",
    },

    "fastapi": {
        "backend development",
        "api development",
    },

    "express": {
        "backend development",
        "api development",
    },

    # Data / ML
    "pandas": {
        "data analysis",
    },

    "numpy": {
        "data analysis",
        "scientific computing",
    },

    "scikit learn": {
        "machine learning",
    },

    "tensorflow": {
        "machine learning",
        "deep learning",
    },

    "pytorch": {
        "machine learning",
        "deep learning",
    },

    "keras": {
        "machine learning",
        "deep learning",
    },

    # Cloud / DevOps
    "docker": {
        "containerization",
        "deployment",
    },

    "kubernetes": {
        "containerization",
        "deployment",
        "orchestration",
    },

    "aws": {
        "cloud computing",
    },

    "azure": {
        "cloud computing",
    },

    "gcp": {
        "cloud computing",
    },

    # Communication / collaboration
    "cross-functional collaboration": {
        "teamwork",
        "stakeholder engagement",
    },

    "team collaboration": {
        "teamwork",
    },

    "research reporting": {
        "communication",
        "storytelling",
    },

    # Strategy / business
    "strategy development": {
        "strategic thinking",
    },

    "business analysis": {
        "business acumen",
    },

    "business analyst": {
        "business acumen",
    },

    # Data / statistics
    "statistical analysis": {
        "statistical software",
    },

    "r": {
        "statistical software",
        "data analysis",
    },

    "sas": {
        "statistical software",
        "data analysis",
    },

    "powerbi": {
        "data visualization",
    },

    "tableau": {
        "data visualization",
    },

    # ML / data science
    "model training": {
        "predictive modeling",
        "machine learning",
    },

    "machine learning leadership": {
        "machine learning",
    },

    "ml system design": {
        "machine learning",
    },

    "algorithm research": {
        "machine learning",
    },

    "data pipeline design": {
        "data preparation",
    },

    "data analysis": {
        "data preparation",
    },

    "data analytics": {
        "data analysis",
    },
}


# -------------------------------------------------------------------
# Related relationships
# -------------------------------------------------------------------
# Mostly symmetric relationships.
#
# Python -> Machine Learning is intentionally directional:
# Python can support ML, but ML does not prove Python.
# -------------------------------------------------------------------

RELATED_SKILLS = {
    ("redux", "react"),
    ("react", "redux"),

    ("javascript", "react"),
    ("react", "javascript"),

    ("typescript", "react"),
    ("react", "typescript"),

    ("docker", "kubernetes"),
    ("kubernetes", "docker"),

    ("fastapi", "api development"),
    ("api development", "fastapi"),

    ("django", "web development"),
    ("web development", "django"),

    ("flask", "web development"),
    ("web development", "flask"),

    ("python", "machine learning"),

    ("tensorflow", "pytorch"),
    ("pytorch", "tensorflow"),

    ("data analytics", "data mining"),
    ("data mining", "data analytics"),

    ("statistical analysis", "statistical software"),
    ("statistical software", "statistical analysis"),

    ("research reporting", "communication"),
    ("communication", "research reporting"),

    ("cross-functional collaboration", "communication"),
    ("communication", "cross-functional collaboration"),

    ("data pipeline design", "data preparation"),
    ("data preparation", "data pipeline design"),
    
}

# -------------------------------------------------------------------
# Adjacent relationships
# -------------------------------------------------------------------
# These are symmetric because either direction means the technologies
# are adjacent/transferable, not equivalent.
# -------------------------------------------------------------------
ADJACENT_SKILLS = {
    # Frontend frameworks
    ("angular", "react"),
    ("react", "angular"),

    ("vue", "react"),
    ("react", "vue"),

    # Programming languages
    ("java", "python"),
    ("python", "java"),

    # Cloud platforms
    ("aws", "azure"),
    ("azure", "aws"),

    ("aws", "gcp"),
    ("gcp", "aws"),

    ("azure", "gcp"),
    ("gcp", "azure"),
}


# -------------------------------------------------------------------
# Normalization
# -------------------------------------------------------------------

def _normalize(text: str) -> str:
    """
    Normalize a skill/concept before comparison.
    """

    value = " ".join(
        str(text)
        .lower()
        .strip()
        .split()
    )

    return ALIASES.get(value, value)


# -------------------------------------------------------------------
# Directional relationship lookup
# -------------------------------------------------------------------

def _pair_exists(
    a: str,
    b: str,
    pairs: set[tuple[str, str]],
) -> bool:
    """
    Directional relationship.

    Example:
        Python -> Machine Learning
        can exist.

    But:
        Machine Learning -> Python
        does not automatically exist.
    """

    return (a, b) in pairs


# -------------------------------------------------------------------
# Symmetric relationship lookup
# -------------------------------------------------------------------

def _symmetric_pair_exists(
    a: str,
    b: str,
    pairs: set[tuple[str, str]],
) -> bool:
    """
    Symmetric relationship.

    Used for adjacent technologies such as:

        Angular <-> React
        AWS <-> Azure
        TensorFlow <-> PyTorch
    """

    return (
        (a, b) in pairs
        or (b, a) in pairs
    )


# -------------------------------------------------------------------
# Capability lookup
# -------------------------------------------------------------------

def _is_capability(
    candidate: str,
    target: str,
) -> bool:
    """
    Check whether candidate skill explicitly supports the target
    capability.
    """

    return target in CAPABILITY_MAP.get(candidate, set())


# -------------------------------------------------------------------
# Sentence Transformer model
# -------------------------------------------------------------------

@lru_cache(maxsize=1)
def _get_model():
    """
    Load the embedding model once and reuse it.
    """

    return SentenceTransformer(MODEL_NAME)


# -------------------------------------------------------------------
# Semantic similarity
# -------------------------------------------------------------------

@lru_cache(maxsize=10000)
def semantic_similarity(
    candidate: str,
    target: str,
) -> float:
    """
    Calculate cosine similarity between two concepts.

    This is ONLY a fallback.

    Explicit relationships always take priority.
    """

    candidate = _normalize(candidate)
    target = _normalize(target)

    if not candidate or not target:
        return 0.0

    model = _get_model()

    embeddings = model.encode(
        [candidate, target],
        normalize_embeddings=True,
    )

    similarity = float(
        embeddings[0] @ embeddings[1]
    )

    return similarity


# -------------------------------------------------------------------
# Main relationship classifier
# -------------------------------------------------------------------

def classify_relationship(
    candidate_skill: str,
    target_skill: str,
) -> dict:
    """
    Determine the relationship between a candidate skill and a
    target job requirement.

    Priority:

    1. EXACT
    2. CAPABILITY
    3. RELATED
    4. ADJACENT
    5. SEMANTIC fallback
    6. UNRELATED
    """

    candidate = _normalize(candidate_skill)
    target = _normalize(target_skill)

    # ---------------------------------------------------------------
    # 1. Empty values
    # ---------------------------------------------------------------

    if not candidate or not target:
        return {
            "candidate_concept": candidate,
            "target_concept": target,
            "relationship": "UNRELATED",
            "semantic_score": 0.0,
            "confidence": 1.0,
            "reason": "One or both concepts are empty.",
        }

    # ---------------------------------------------------------------
    # 2. EXACT
    # ---------------------------------------------------------------

    if candidate == target:
        return {
            "candidate_concept": candidate,
            "target_concept": target,
            "relationship": "EXACT",
            "semantic_score": 1.0,
            "confidence": 1.0,
            "reason": (
                "Candidate and target concepts normalize to "
                "the same skill."
            ),
        }

    # ---------------------------------------------------------------
    # 3. CAPABILITY
    # ---------------------------------------------------------------

    if _is_capability(candidate, target):
        return {
            "candidate_concept": candidate,
            "target_concept": target,
            "relationship": "CAPABILITY",
            "semantic_score": 0.85,
            "confidence": 0.90,
            "reason": (
                f"{candidate} is an explicit capability "
                f"supporting {target}."
            ),
        }

    # ---------------------------------------------------------------
    # 4. RELATED
    # ---------------------------------------------------------------

    if _pair_exists(
        candidate,
        target,
        RELATED_SKILLS,
    ):
        return {
            "candidate_concept": candidate,
            "target_concept": target,
            "relationship": "RELATED",
            "semantic_score": 0.72,
            "confidence": 0.85,
            "reason": (
                f"{candidate} is explicitly related "
                f"to {target}."
            ),
        }

    # ---------------------------------------------------------------
    # 5. ADJACENT
    # ---------------------------------------------------------------

    if _symmetric_pair_exists(
        candidate,
        target,
        ADJACENT_SKILLS,
    ):
        return {
            "candidate_concept": candidate,
            "target_concept": target,
            "relationship": "ADJACENT",
            "semantic_score": 0.45,
            "confidence": 0.80,
            "reason": (
                f"{candidate} and {target} are adjacent "
                f"technologies or skills."
            ),
        }

    # ---------------------------------------------------------------
    # 6. Semantic fallback
    # ---------------------------------------------------------------

    similarity = semantic_similarity(
        candidate,
        target,
    )

    if similarity >= 0.82:

        relationship = "SEMANTIC"

        confidence = min(
            0.90,
            similarity,
        )

        reason = (
            f"Semantic similarity suggests that "
            f"{candidate} and {target} are conceptually related."
        )

    elif similarity >= 0.68:

        relationship = "ADJACENT"

        confidence = min(
            0.75,
            similarity,
        )

        reason = (
            f"Semantic similarity suggests an adjacent "
            f"relationship between {candidate} and {target}."
        )

    else:

        relationship = "UNRELATED"

        confidence = max(
            0.0,
            similarity,
        )

        reason = (
            f"No explicit relationship was found and "
            f"semantic similarity is low."
        )

    # ---------------------------------------------------------------
    # 7. Final result
    # ---------------------------------------------------------------

    return {
        "candidate_concept": candidate,
        "target_concept": target,
        "relationship": relationship,
        "semantic_score": round(
            similarity,
            4,
        ),
        "confidence": round(
            confidence,
            4,
        ),
        "reason": reason,
    }