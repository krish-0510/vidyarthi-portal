"""
analytics.py — Vidyarthi Portal
Computes and returns structured analytics from the student Excel data.
"""

import pandas as pd
import re
from datetime import date


def _safe(val):
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return ""
    s = str(val).strip()
    if re.match(r"^\d+\.0$", s):
        s = s[:-2]
    return s


def load_dataframe(excel_path: str) -> pd.DataFrame:
    """Load the best available sheet from the Excel file."""
    xf = pd.ExcelFile(excel_path)
    sheet = (
        "CALCULATED STUDENTS DATA"
        if "CALCULATED STUDENTS DATA" in xf.sheet_names
        else "STUDENTS DATA"
    )
    df = pd.read_excel(excel_path, sheet_name=sheet)
    df = df.dropna(subset=["STUDENT NAME"])
    return df


def compute_analytics(excel_path: str) -> dict:
    """
    Return a dict with all analytics:
    - summary counts
    - gender distribution
    - caste/category breakdown
    - religion distribution
    - subject-wise distribution
    - age statistics
    - per-student table
    """
    df = load_dataframe(excel_path)

    total = len(df)

    # ── Gender ──────────────────────────────
    gender_counts = df["M/F"].str.strip().str.upper().value_counts().to_dict()
    male   = gender_counts.get("M", 0)
    female = gender_counts.get("F", 0)

    # ── Caste ───────────────────────────────
    caste_col = "CASTE"
    caste_counts = (
        df[caste_col].str.strip().str.upper().value_counts().to_dict()
        if caste_col in df.columns else {}
    )

    # ── Religion ────────────────────────────
    rel_counts = (
        df["RELIGION"].str.strip().str.upper().value_counts().to_dict()
        if "RELIGION" in df.columns else {}
    )

    # ── Subjects ────────────────────────────
    subj_col = "SUBJECT OPTED"
    subject_counts = (
        df[subj_col].str.strip().str.upper().value_counts().to_dict()
        if subj_col in df.columns else {}
    )

    # ── Age distribution ─────────────────────
    ages = []
    dob_col = "DATE OF BIRTH"
    today = date.today()
    for v in df[dob_col].dropna():
        try:
            s = str(v).strip()
            # Try multiple formats
            for fmt in ("%d.%m.%Y", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
                try:
                    d = pd.to_datetime(s, format=fmt).date()
                    age = today.year - d.year - ((today.month, today.day) < (d.month, d.day))
                    ages.append(age)
                    break
                except Exception:
                    continue
        except Exception:
            continue

    age_stats = {
        "min": min(ages) if ages else None,
        "max": max(ages) if ages else None,
        "avg": round(sum(ages) / len(ages), 1) if ages else None,
        "distribution": {},
    }
    for a in ages:
        age_stats["distribution"][a] = age_stats["distribution"].get(a, 0) + 1

    # ── Per-student table ────────────────────
    students = []
    for _, row in df.iterrows():
        students.append(
            {
                "sr_no":      _safe(row.get("SR. NO.")),
                "name":       _safe(row.get("STUDENT NAME")),
                "father":     _safe(row.get("FATHER'S NAME")),
                "mother":     _safe(row.get("MOTHER'S NAME")),
                "gender":     _safe(row.get("M/F")),
                "dob":        _safe(row.get("DATE OF BIRTH")),
                "caste":      _safe(row.get("CASTE")),
                "religion":   _safe(row.get("RELIGION")),
                "subject":    _safe(row.get("SUBJECT OPTED")),
                "adm_no":     _safe(row.get("ADM NO")),
                "address":    _safe(row.get("CORRESPONDENCE ADDRESS")),
                "email":      _safe(row.get("EMAIL ID ") or row.get("EMAIL ID") or ""),
            }
        )

    return {
        "total":           total,
        "male":            male,
        "female":          female,
        "caste":           caste_counts,
        "religion":        rel_counts,
        "subjects":        subject_counts,
        "age_stats":       age_stats,
        "students":        students,
    }


if __name__ == "__main__":
    import sys, json
    excel = sys.argv[1] if len(sys.argv) > 1 else "CLASS_12_STUDENTS_PROFILE_2026-27.xlsx"
    result = compute_analytics(excel)
    # Pretty-print summary
    print(f"\n{'='*50}")
    print(f"  VIDYARTHI PORTAL — STUDENT ANALYTICS")
    print(f"{'='*50}")
    print(f"  Total Students  : {result['total']}")
    print(f"  Male            : {result['male']}")
    print(f"  Female          : {result['female']}")
    print(f"\n  CASTE BREAKDOWN:")
    for k, v in result["caste"].items():
        print(f"    {k:10s}: {v}")
    print(f"\n  RELIGION:")
    for k, v in result["religion"].items():
        print(f"    {k:10s}: {v}")
    print(f"\n  SUBJECTS:")
    for k, v in result["subjects"].items():
        print(f"    {k:15s}: {v}")
    print(f"\n  AGE STATS:")
    a = result["age_stats"]
    print(f"    Min: {a['min']}  Max: {a['max']}  Avg: {a['avg']}")
    print(f"{'='*50}\n")
