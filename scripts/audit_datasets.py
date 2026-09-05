from pathlib import Path
import ast
import json
import re
import pandas as pd


# ============================================================
# Resume Matching Engine - Dataset Audit
# Step 11: Dataset Acquisition + Quality Audit
# ============================================================

ROOT = Path(__file__).resolve().parents[1]

DATASETS = {
    "resume_ranking": ROOT / "data" / "raw" / "resume_ranking" / "resume_data_for_ranking.csv",
    "job_skill_set": ROOT / "data" / "raw" / "job_skill_set" / "all_job_post.csv",
}

AUDIT_MD = ROOT / "data" / "DATASET_AUDIT.md"
AUDIT_JSON = ROOT / "data" / "interim" / "audit_summary.json"


def load_csv(path):
    """Load CSV with a UTF-8 fallback."""
    try:
        return pd.read_csv(path, low_memory=False)
    except UnicodeDecodeError:
        return pd.read_csv(
            path,
            encoding="latin1",
            low_memory=False
        )


def normalize_text(value):
    """Normalize text for duplicate/leakage analysis only."""
    if pd.isna(value):
        return ""

    value = str(value).lower()
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def is_empty(value):
    if pd.isna(value):
        return True

    if isinstance(value, str):
        return not value.strip()

    return False


def column_missing_stats(df):
    results = {}

    for column in df.columns:
        missing = df[column].apply(is_empty).sum()
        percentage = (missing / len(df) * 100) if len(df) else 0

        results[column] = {
            "missing_or_empty": int(missing),
            "percentage": round(percentage, 2),
        }

    return results


def text_length_stats(df):
    results = {}

    for column in df.columns:
        if df[column].dtype != "object":
            continue

        lengths = (
            df[column]
            .fillna("")
            .astype(str)
            .str.len()
        )

        if len(lengths) == 0:
            continue

        results[column] = {
            "min": int(lengths.min()),
            "median": float(lengths.median()),
            "mean": round(float(lengths.mean()), 2),
            "max": int(lengths.max()),
        }

    return results


def list_like_stats(df):
    """
    Detect fields that look like Python/JSON lists and test
    whether their contents can be parsed safely.
    """

    results = {}

    for column in df.columns:
        if df[column].dtype != "object":
            continue

        series = df[column].dropna().astype(str)

        if len(series) == 0:
            continue

        list_like = series[
            series.str.strip().str.startswith("[")
            & series.str.strip().str.endswith("]")
        ]

        if len(list_like) == 0:
            continue

        valid = 0
        invalid = 0

        for value in list_like:
            try:
                parsed = ast.literal_eval(value)

                if isinstance(parsed, list):
                    valid += 1
                else:
                    invalid += 1

            except Exception:
                invalid += 1

        results[column] = {
            "list_like_values": int(len(list_like)),
            "valid_lists": int(valid),
            "invalid_lists": int(invalid),
        }

    return results


def signature(df, columns):
    """
    Create an in-memory normalized signature.
    This NEVER modifies the original dataframe/file.
    """

    available = [c for c in columns if c in df.columns]

    if not available:
        return pd.Series([""] * len(df), index=df.index)

    combined = (
        df[available]
        .fillna("")
        .astype(str)
        .apply(
            lambda row: " | ".join(
                normalize_text(value)
                for value in row
            ),
            axis=1,
        )
    )

    return combined


def repeated_signature_stats(df, columns):
    sig = signature(df, columns)

    if len(sig) == 0:
        return {
            "unique_signatures": 0,
            "repeated_rows": 0,
            "groups_with_repetition": 0,
        }

    counts = sig.value_counts()

    repeated_groups = counts[counts > 1]

    repeated_rows = int(
        repeated_groups.sum() - len(repeated_groups)
    )

    return {
        "unique_signatures": int(sig.nunique()),
        "repeated_rows": repeated_rows,
        "groups_with_repetition": int(len(repeated_groups)),
    }


def top_values(df, column, n=15):
    if column not in df.columns:
        return {}

    values = (
        df[column]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    values = values[values != ""]

    return {
        str(key): int(value)
        for key, value in values.value_counts().head(n).items()
    }


def score_stats(df):
    if "matched_score" not in df.columns:
        return None

    numeric = pd.to_numeric(
        df["matched_score"],
        errors="coerce"
    ).dropna()

    if len(numeric) == 0:
        return {
            "available": False,
            "reason": "matched_score exists but contains no numeric values",
        }

    return {
        "available": True,
        "count": int(len(numeric)),
        "min": round(float(numeric.min()), 4),
        "max": round(float(numeric.max()), 4),
        "mean": round(float(numeric.mean()), 4),
        "median": round(float(numeric.median()), 4),
        "std": round(float(numeric.std()), 4),
        "percentiles": {
            "p01": round(float(numeric.quantile(0.01)), 4),
            "p05": round(float(numeric.quantile(0.05)), 4),
            "p25": round(float(numeric.quantile(0.25)), 4),
            "p50": round(float(numeric.quantile(0.50)), 4),
            "p75": round(float(numeric.quantile(0.75)), 4),
            "p95": round(float(numeric.quantile(0.95)), 4),
            "p99": round(float(numeric.quantile(0.99)), 4),
        },
        "unique_values": int(numeric.nunique()),
    }


def score_variation_by_signature(df, signature_columns):
    """
    Detect whether identical normalized resume/job information
    appears with different matched scores.

    This is important for leakage/label-quality investigation.
    """

    if "matched_score" not in df.columns:
        return None

    numeric_score = pd.to_numeric(
        df["matched_score"],
        errors="coerce"
    )

    sig = signature(df, signature_columns)

    temp = pd.DataFrame({
        "signature": sig,
        "score": numeric_score
    })

    temp = temp.dropna(subset=["score"])

    if temp.empty:
        return None

    grouped = temp.groupby("signature")["score"].nunique()

    varying = grouped[grouped > 1]

    return {
        "groups_checked": int(len(grouped)),
        "groups_with_multiple_scores": int(len(varying)),
    }


def audit_dataset(name, path):
    print("\n" + "=" * 70)
    print(f"AUDITING: {name}")
    print("=" * 70)

    if not path.exists():
        raise FileNotFoundError(
            f"Dataset not found: {path}"
        )

    file_size = path.stat().st_size

    df = load_csv(path)

    print(f"File: {path}")
    print(f"File size: {file_size:,} bytes")
    print(f"Rows: {len(df):,}")
    print(f"Columns: {len(df.columns)}")

    print("\nColumns:")
    for column in df.columns:
        print(f"  - {column}")

    print("\nDtypes:")
    for column, dtype in df.dtypes.items():
        print(f"  - {column}: {dtype}")

    missing = column_missing_stats(df)

    print("\nMissing / Empty values:")
    for column, stats in missing.items():
        if stats["missing_or_empty"] > 0:
            print(
                f"  - {column}: "
                f"{stats['missing_or_empty']:,} "
                f"({stats['percentage']}%)"
            )

    duplicate_rows = int(df.duplicated().sum())

    print(f"\nExact duplicate rows: {duplicate_rows:,}")

    result = {
        "name": name,
        "path": str(path.relative_to(ROOT)),
        "file_size_bytes": int(file_size),
        "rows": int(len(df)),
        "columns_count": int(len(df.columns)),
        "columns": list(df.columns),
        "dtypes": {
            str(k): str(v)
            for k, v in df.dtypes.items()
        },
        "missing": missing,
        "exact_duplicate_rows": duplicate_rows,
        "text_length_stats": text_length_stats(df),
        "list_like_stats": list_like_stats(df),
    }

    return df, result


def main():
    print("\nResume Matching Engine")
    print("Step 11 - Dataset Audit")
    print("=" * 70)

    AUDIT_JSON.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    audit_results = {}

    # --------------------------------------------------------
    # Dataset A: Resume Data for Ranking
    # --------------------------------------------------------

    resume_df, resume_result = audit_dataset(
        "resume_ranking",
        DATASETS["resume_ranking"]
    )

    resume_columns = [
        "career_objective",
        "skills",
        "educational_institution_name",
        "degree_names",
        "passing_years",
        "major_field_of_studies",
        "educational_results",
        "professional_company_names",
        "positions",
        "responsibilities",
        "certification_providers",
        "certification_skills",
        "languages",
        "proficiency_levels",
        "extra_curricular_activity_types",
        "extra_curricular_organization_names",
        "role_positions",
    ]

    job_columns = [
        "job_position_name",
        "educationaL_requirements",
        "experiencere_requirement",
        "age_requirement",
        "skills_required",
        "responsibilities.1",
    ]

    resume_result["resume_signature_analysis"] = (
        repeated_signature_stats(
            resume_df,
            resume_columns
        )
    )

    resume_result["job_signature_analysis"] = (
        repeated_signature_stats(
            resume_df,
            job_columns
        )
    )

    resume_result["matched_score_stats"] = score_stats(
        resume_df
    )

    resume_result["resume_score_variation"] = (
        score_variation_by_signature(
            resume_df,
            resume_columns
        )
    )

    resume_result["job_score_variation"] = (
        score_variation_by_signature(
            resume_df,
            job_columns
        )
    )

    resume_result["top_job_titles"] = top_values(
        resume_df,
        "job_position_name"
    )

    audit_results["resume_ranking"] = resume_result

    # --------------------------------------------------------
    # Dataset B: Job Skill Set
    # --------------------------------------------------------

    job_df, job_result = audit_dataset(
        "job_skill_set",
        DATASETS["job_skill_set"]
    )

    job_result["top_categories"] = top_values(
        job_df,
        "category"
    )

    job_result["top_job_titles"] = top_values(
        job_df,
        "job_title"
    )

    if "job_id" in job_df.columns:
        job_result["unique_job_ids"] = int(
            job_df["job_id"].nunique()
        )

        job_result["duplicate_job_ids"] = int(
            job_df["job_id"].duplicated().sum()
        )

    job_result["job_description_repetition"] = (
        repeated_signature_stats(
            job_df,
            [
                "job_title",
                "job_description",
            ]
        )
    )

    audit_results["job_skill_set"] = job_result

    # --------------------------------------------------------
    # Save JSON
    # --------------------------------------------------------

    with open(
        AUDIT_JSON,
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            audit_results,
            f,
            indent=2,
            ensure_ascii=False
        )

    # --------------------------------------------------------
    # Build Markdown report
    # --------------------------------------------------------

    lines = []

    lines.append("# Dataset Audit Report")
    lines.append("")
    lines.append(
        "Generated automatically for the "
        "Explainable Hybrid Resume–Job Matching Engine."
    )
    lines.append("")
    lines.append(
        "**Important:** Raw datasets were only read during this "
        "audit. No raw CSV was modified."
    )
    lines.append("")

    for name, result in audit_results.items():

        lines.append(f"## {name}")
        lines.append("")

        lines.append(
            f"- **Rows:** {result['rows']:,}"
        )
        lines.append(
            f"- **Columns:** {result['columns_count']}"
        )
        lines.append(
            f"- **File size:** "
            f"{result['file_size_bytes']:,} bytes"
        )
        lines.append(
            f"- **Exact duplicate rows:** "
            f"{result['exact_duplicate_rows']:,}"
        )
        lines.append("")

        lines.append("### Columns")
        lines.append("")

        for column in result["columns"]:
            dtype = result["dtypes"][column]
            lines.append(
                f"- `{column}` — `{dtype}`"
            )

        lines.append("")

        lines.append("### Missing / Empty Values")
        lines.append("")

        lines.append(
            "| Column | Missing/Empty | Percentage |"
        )
        lines.append(
            "|---|---:|---:|"
        )

        for column, stats in result["missing"].items():
            lines.append(
                f"| `{column}` | "
                f"{stats['missing_or_empty']:,} | "
                f"{stats['percentage']}% |"
            )

        lines.append("")

        lines.append("### Text Length Statistics")
        lines.append("")
        lines.append(
            "| Column | Min | Median | Mean | Max |"
        )
        lines.append(
            "|---|---:|---:|---:|---:|"
        )

        for column, stats in result[
            "text_length_stats"
        ].items():
            lines.append(
                f"| `{column}` | "
                f"{stats['min']} | "
                f"{stats['median']} | "
                f"{stats['mean']} | "
                f"{stats['max']} |"
            )

        lines.append("")

        if result.get("matched_score_stats"):
            lines.append("### Matched Score Analysis")
            lines.append("")

            score = result["matched_score_stats"]

            if score.get("available"):
                lines.append(
                    f"- Count: {score['count']:,}"
                )
                lines.append(
                    f"- Min: {score['min']}"
                )
                lines.append(
                    f"- Max: {score['max']}"
                )
                lines.append(
                    f"- Mean: {score['mean']}"
                )
                lines.append(
                    f"- Median: {score['median']}"
                )
                lines.append(
                    f"- Unique values: "
                    f"{score['unique_values']:,}"
                )

                lines.append("")
                lines.append("Percentiles:")

                for key, value in score[
                    "percentiles"
                ].items():
                    lines.append(
                        f"- {key}: {value}"
                    )

            else:
                lines.append(
                    f"- {score.get('reason')}"
                )

            lines.append("")

        if "resume_signature_analysis" in result:
            lines.append(
                "### Resume Repetition Analysis"
            )
            lines.append("")

            stats = result[
                "resume_signature_analysis"
            ]

            lines.append(
                f"- Unique normalized resume signatures: "
                f"{stats['unique_signatures']:,}"
            )
            lines.append(
                f"- Groups with repetition: "
                f"{stats['groups_with_repetition']:,}"
            )
            lines.append(
                f"- Repeated rows beyond first occurrence: "
                f"{stats['repeated_rows']:,}"
            )
            lines.append("")

        if "job_signature_analysis" in result:
            lines.append(
                "### Job Repetition Analysis"
            )
            lines.append("")

            stats = result[
                "job_signature_analysis"
            ]

            lines.append(
                f"- Unique normalized job signatures: "
                f"{stats['unique_signatures']:,}"
            )
            lines.append(
                f"- Groups with repetition: "
                f"{stats['groups_with_repetition']:,}"
            )
            lines.append(
                f"- Repeated rows beyond first occurrence: "
                f"{stats['repeated_rows']:,}"
            )
            lines.append("")

        if "resume_score_variation" in result:
            lines.append(
                "### Potential Label Leakage Investigation"
            )
            lines.append("")

            lines.append(
                "Resume groups with multiple matched scores:"
            )
            lines.append(
                f"- "
                f"{result['resume_score_variation']['groups_with_multiple_scores']:,}"
            )
            lines.append("")

            lines.append(
                "Job groups with multiple matched scores:"
            )
            lines.append(
                f"- "
                f"{result['job_score_variation']['groups_with_multiple_scores']:,}"
            )
            lines.append("")

        if "top_categories" in result:
            lines.append("### Top Categories")
            lines.append("")

            for value, count in result[
                "top_categories"
            ].items():
                lines.append(
                    f"- {value}: {count:,}"
                )

            lines.append("")

        if "top_job_titles" in result:
            lines.append("### Top Job Titles")
            lines.append("")

            for value, count in result[
                "top_job_titles"
            ].items():
                lines.append(
                    f"- {value}: {count:,}"
                )

            lines.append("")

    lines.append("## Initial Audit Interpretation")
    lines.append("")
    lines.append(
        "This report is a structural and quality audit only. "
        "The `matched_score` field, if present, must not automatically "
        "be treated as ground-truth hiring truth."
    )
    lines.append("")
    lines.append(
        "The primary evaluation truth for this project will be "
        "our requirement-level and adversarial gold-label dataset."
    )
    lines.append("")
    lines.append(
        "Raw datasets remain immutable. Any preprocessing will be "
        "performed into `data/interim/` or `data/processed/`."
    )
    lines.append("")

    with open(
        AUDIT_MD,
        "w",
        encoding="utf-8"
    ) as f:
        f.write("\n".join(lines))

    print("\n" + "=" * 70)
    print("AUDIT COMPLETE")
    print("=" * 70)

    print(f"\nCreated:")
    print(f"  {AUDIT_MD}")
    print(f"  {AUDIT_JSON}")

    print("\nRaw datasets were NOT modified.")


if __name__ == "__main__":
    main()