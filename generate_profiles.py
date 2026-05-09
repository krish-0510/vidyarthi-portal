"""
generate_profiles.py — Vidyarthi Portal
Generates individual student profile PDFs from Excel data,
then merges them into one combined PDF.
"""

import os
import re
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from pypdf import PdfWriter, PdfReader

W, H = A4  # 595.27 x 841.89 pts


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def safe(val, as_str=True):
    """Return clean string or '' for NaN / None values."""
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return ""
    s = str(val).strip()
    # Remove .0 suffix from numbers stored as float
    if re.match(r'^\d+\.0$', s):
        s = s[:-2]
    return s


def fmt_mobile(val):
    """Format a mobile number stored as scientific float or plain string."""
    s = safe(val)
    if not s:
        return ""
    try:
        n = int(float(s))
        return str(n)
    except Exception:
        return s


def wrap_text(text, max_chars=58):
    """Split long address into two lines."""
    if len(text) <= max_chars:
        return [text, ""]
    # Try to break at a space near the midpoint
    mid = len(text) // 2
    for i in range(mid, 0, -1):
        if text[i] == " ":
            return [text[:i], text[i+1:]]
    return [text[:max_chars], text[max_chars:]]


# ─────────────────────────────────────────────
# Per-page drawing
# ─────────────────────────────────────────────

def draw_profile(c: canvas.Canvas, row: dict):
    """Draw one student profile on the current canvas page."""

    ML = 1.8 * cm
    MR = 1.8 * cm
    MT = 1.2 * cm
    MB = 1.2 * cm

    # ── outer border ──────────────────────────
    c.setLineWidth(1.8)
    c.rect(ML - 0.4 * cm, MB, W - ML - MR + 0.4 * cm, H - MT - MB - 0.2 * cm)

    # ── school header ────────────────────────
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(W / 2, H - MT - 0.85 * cm, "PM SHRI KENDRIYA VIDYALAYA AFS WADSAR")
    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(W / 2, H - MT - 1.6 * cm, "Student's Profile")
    c.setFont("Helvetica", 10)
    c.drawCentredString(W / 2, H - MT - 2.2 * cm, "(CLASS XII SCIENCE 2026-27)")

    # ── divider ───────────────────────────────
    c.setLineWidth(0.8)
    c.line(ML, H - MT - 2.6 * cm, W - MR, H - MT - 2.6 * cm)

    # ── photo box ────────────────────────────
    PW, PH = 3.6 * cm, 4.5 * cm
    PHOTO_INSET = 0.15 * cm
    PHOTO_GUTTER = 0.5 * cm
    PX = W - MR - PHOTO_INSET - PW
    PY = H - MT - 2.6 * cm - PH - 0.3 * cm
    c.setLineWidth(1)
    c.rect(PX, PY, PW, PH)
    c.setFont("Helvetica", 8)
    c.setFillColorRGB(0.55, 0.55, 0.55)
    c.drawCentredString(PX + PW / 2, PY + PH / 2 - 0.15 * cm, "Paste Photo")
    c.setFillColorRGB(0, 0, 0)

    # ── field renderer ───────────────────────
    FIELD_START_Y = H - MT - 3.05 * cm
    SIGNATURE_Y = MB + 1.7 * cm
    LH = (FIELD_START_Y - SIGNATURE_Y) / 18.3
    FONT_SIZE = 11.2
    LABEL_FONT = "Helvetica-Bold"
    VALUE_FONT = "Helvetica"

    def _right_edge_for(y):
        row_top = y + FONT_SIZE
        row_bottom = y - 0.18 * cm
        if row_top >= PY and row_bottom <= PY + PH:
            return PX - PHOTO_GUTTER
        return W - MR

    def _underline(x1, y, x2):
        if x2 <= x1:
            return
        c.setLineWidth(0.4)
        c.line(x1, y - 0.13 * cm, x2, y - 0.13 * cm)

    def field(label, value, y, x1=None, x2=None):
        x1 = x1 if x1 is not None else ML
        x2 = min(x2 if x2 is not None else _right_edge_for(y), _right_edge_for(y))

        c.setFont(LABEL_FONT, FONT_SIZE)
        lw = c.stringWidth(label, LABEL_FONT, FONT_SIZE)
        c.drawString(x1, y, label)

        vx = x1 + lw + 0.25 * cm
        _underline(vx, y, x2)
        if value:
            c.setFont(VALUE_FONT, FONT_SIZE)
            # Clip to available width
            avail = x2 - vx - 0.2 * cm
            c.drawString(vx + 0.15 * cm, y, _clip(value, VALUE_FONT, FONT_SIZE, avail, c))

    def pair(label1, val1, label2, val2, y, split=0.5):
        right_edge = _right_edge_for(y)
        mid = ML + (right_edge - ML) * split
        field(label1, val1, y, x1=ML, x2=mid - 0.3 * cm)
        field(label2, val2, y, x1=mid, x2=right_edge)

    def _clip(text, font, size, max_w, canv):
        """Truncate text with ellipsis if it exceeds max_w."""
        if max_w <= 0:
            return ""
        ellipsis = "…"
        if canv.stringWidth(text, font, size) <= max_w:
            return text
        if canv.stringWidth(ellipsis, font, size) > max_w:
            return ""
        while text and canv.stringWidth(text + ellipsis, font, size) > max_w:
            text = text[:-1]
        return text + ellipsis

    # ── extract student data ──────────────────
    name         = safe(row.get("STUDENT NAME"))
    father       = safe(row.get("FATHER'S NAME"))
    mother       = safe(row.get("MOTHER'S NAME"))
    adm_no       = safe(row.get("ADM NO"))
    dob          = safe(row.get("DATE OF BIRTH"))
    address      = safe(row.get("CORRESPONDENCE ADDRESS"))
    gender_raw   = safe(row.get("M/F", ""))
    gender       = "Male" if gender_raw.upper() == "M" else "Female" if gender_raw.upper() == "F" else gender_raw
    religion     = safe(row.get("RELIGION"))
    caste        = safe(row.get("CASTE"))
    subjects     = safe(row.get("SUBJECT OPTED"))
    email        = safe(row.get("EMAIL ID ") or row.get("EMAIL ID") or "")
    adhar        = safe(row.get("ADHAR NO"))
    blood_group  = safe(row.get("BLOOD GROUP", ""))
    domicile     = safe(row.get("DOMICILE STATE", ""))
    income       = safe(row.get("MONTHLY INCOME", ""))
    apar         = safe(row.get("APAR NO", ""))
    house        = safe(row.get("HOUSE", ""))
    f_prof       = safe(row.get("FATHER'S PROFESSION", ""))
    m_prof       = safe(row.get("MOTHER'S PROFESSION", ""))

    f_mobile     = fmt_mobile(row.get("MOBILE \n(FATHER)") or row.get("MOBILE NO"))
    m_mobile     = fmt_mobile(row.get("MOBILE NO\n(MOTHER)", ""))
    p_mobile     = f_mobile  # personal = father's as per sample

    addr1, addr2 = wrap_text(address)

    # ── draw fields ──────────────────────────
    y = FIELD_START_Y

    field("Name of the Student:",  name,   y)
    y -= LH
    field("Father's Name:",        father, y)
    y -= LH
    field("Mother's Name:",        mother, y)
    y -= LH

    # Admission No + DOB (same line)
    adm_right = _right_edge_for(y)
    mid_adm = ML + (adm_right - ML) * 0.44
    field("Admission No:",  adm_no, y, x1=ML, x2=mid_adm)
    field("Date of Birth",  dob,    y, x1=mid_adm + 0.1 * cm, x2=adm_right)
    y -= LH

    # Address – 2 lines
    field("Address:", addr1, y)
    y -= LH
    field("", addr2, y)
    y -= LH

    # Mobile row – manual layout
    c.setFont(LABEL_FONT, FONT_SIZE)
    c.drawString(ML, y, "Mobile No:")
    lw0 = c.stringWidth("Mobile No:", LABEL_FONT, FONT_SIZE)
    cx = ML + lw0 + 0.3 * cm

    def _mobile_segment(label, value, start_x, end_x, y):
        c.setFont(LABEL_FONT, FONT_SIZE)
        c.drawString(start_x, y, label)
        lw = c.stringWidth(label, LABEL_FONT, FONT_SIZE)
        vx = start_x + lw + 0.15 * cm
        _underline(vx, y, end_x)
        if value:
            c.setFont(VALUE_FONT, FONT_SIZE)
            avail = end_x - vx - 0.1 * cm
            c.drawString(vx + 0.1 * cm, y, _clip(value[:12], VALUE_FONT, FONT_SIZE, avail, c))
        return end_x

    mobile_right = _right_edge_for(y)
    seg_w = (mobile_right - cx) / 3
    _mobile_segment("Personal:", p_mobile, cx,           cx + seg_w - 0.2*cm,           y)
    _mobile_segment("Father:",   f_mobile, cx + seg_w,   cx + 2*seg_w - 0.2*cm,         y)
    _mobile_segment("Mother:",   m_mobile, cx + 2*seg_w, mobile_right,                  y)
    y -= LH

    pair("Blood Group:",    blood_group, "Domicile State:", domicile, y)
    y -= LH
    pair("Gender: Male/Female", gender,  "Religion:",      religion, y)
    y -= LH
    pair("Monthly Income:", income,      "APAR NO:",       apar,     y)
    y -= LH

    field("Father's Profession and Address:", f_prof, y)
    y -= LH
    field("", "", y)
    y -= LH

    field("Mother's Profession and Address:", m_prof, y)
    y -= LH
    field("", "", y)
    y -= LH

    field("Subjects Opted:", subjects, y)
    y -= LH

    pair("House:", house, "Adhar No:", adhar, y)
    y -= LH

    # Caste with note
    c.setFont(LABEL_FONT, FONT_SIZE)
    c.drawString(ML, y, "Caste:")
    lw_caste = c.stringWidth("Caste:", LABEL_FONT, FONT_SIZE)
    note = "   (Attach Certificate incase of SC/ST/OBC)"
    mid_c = W / 2 - 1.5 * cm
    _underline(ML + lw_caste + 0.2 * cm, y, mid_c)
    if caste:
        c.setFont(VALUE_FONT, FONT_SIZE)
        c.drawString(ML + lw_caste + 0.35 * cm, y, caste)
    c.setFont("Helvetica", 8.5)
    c.drawString(mid_c + 0.2 * cm, y, note)
    y -= LH

    field("Email Address:", email, y)
    y -= 1.3 * LH

    # ── signatures ───────────────────────────
    c.setFont(LABEL_FONT, FONT_SIZE)
    c.drawString(ML, y, "Student's Signature")
    c.drawString(W - MR - 4.2 * cm, y, "Parent's signature")
    c.setLineWidth(0.5)
    c.line(ML, y - 0.15 * cm, ML + 4 * cm, y - 0.15 * cm)
    c.line(W - MR - 4.2 * cm, y - 0.15 * cm, W - MR, y - 0.15 * cm)


# ─────────────────────────────────────────────
# Main: Load Excel → generate PDFs → merge
# ─────────────────────────────────────────────

def generate_all_profiles(excel_path: str, output_dir: str = "output") -> str:
    """
    Read Excel, generate one PDF per student, merge into a single PDF.
    Returns the path to the merged PDF.
    """
    os.makedirs(output_dir, exist_ok=True)
    individual_dir = os.path.join(output_dir, "individual")
    os.makedirs(individual_dir, exist_ok=True)

    # Prefer the richer sheet; fall back to basic sheet
    xf = pd.ExcelFile(excel_path)
    sheet = "CALCULATED STUDENTS DATA" if "CALCULATED STUDENTS DATA" in xf.sheet_names else "STUDENTS DATA"
    df = pd.read_excel(excel_path, sheet_name=sheet)
    df = df.dropna(subset=["STUDENT NAME"])

    individual_pdfs = []

    for idx, row in df.iterrows():
        row_dict = row.to_dict()
        name_slug = re.sub(r"[^\w]", "_", safe(row_dict.get("STUDENT NAME", f"student_{idx}")))
        out_path = os.path.join(individual_dir, f"{idx+1:03d}_{name_slug}.pdf")

        c = canvas.Canvas(out_path, pagesize=A4)
        draw_profile(c, row_dict)
        c.showPage()
        c.save()

        individual_pdfs.append(out_path)
        print(f"  ✓  Generated: {os.path.basename(out_path)}")

    # ── merge all into one PDF ────────────────
    merged_path = os.path.join(output_dir, "ALL_STUDENT_PROFILES.pdf")
    writer = PdfWriter()
    for pdf in individual_pdfs:
        reader = PdfReader(pdf)
        for page in reader.pages:
            writer.add_page(page)

    with open(merged_path, "wb") as f:
        writer.write(f)

    print(f"\n✅ Merged PDF saved → {merged_path}  ({len(individual_pdfs)} profiles)")
    return merged_path


if __name__ == "__main__":
    import sys
    excel = sys.argv[1] if len(sys.argv) > 1 else "CLASS_12_STUDENTS_PROFILE_2026-27.xlsx"
    generate_all_profiles(excel)
