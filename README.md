# Vidyarthi Portal
### PM Shri Kendriya Vidyalaya AFS Wadsar — Class XII Student Profile System

A full-stack web application that:
- Parses student data from the official Excel sheet
- Displays interactive analytics (gender, caste, religion, subjects, age)
- Generates individual student profile PDFs matching the official format
- Merges all profiles into a single downloadable PDF

---

## Project Structure

```
vidyarthi-portal/
├── app.py                   # Flask backend (routes, upload, generate, download)
├── generate_profiles.py     # PDF profile generator (reportlab + pypdf)
├── analytics.py             # Student data analytics engine
├── requirements.txt
├── README.md
├── static/
│   ├── css/style.css        # Full UI stylesheet
│   └── js/main.js           # Frontend: upload, charts, table, PDF trigger
└── templates/
    └── index.html           # Main page template
```

---

## Setup & Run

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the web server
```bash
python app.py
```
Then open **http://localhost:5000** in your browser.

### 3. Use the portal
1. Upload the Excel file (`CLASS_12_STUDENTS_PROFILE_2026-27.xlsx`)
2. View analytics dashboard (charts auto-render)
3. Browse the student directory — search by name, subject, caste, etc.
4. Click **Generate & Merge PDF** to create all profiles
5. Click **Download PDF** to save `ALL_STUDENT_PROFILES.pdf`

---

## Standalone Scripts (no server needed)

### Generate PDFs only
```bash
python generate_profiles.py CLASS_12_STUDENTS_PROFILE_2026-27.xlsx
```
Output: `output/ALL_STUDENT_PROFILES.pdf` + individual PDFs in `output/individual/`

### View analytics in terminal
```bash
python analytics.py CLASS_12_STUDENTS_PROFILE_2026-27.xlsx
```

---

## Excel Sheet Format Expected

The script reads from **CALCULATED STUDENTS DATA** sheet (falls back to **STUDENTS DATA**).

Key columns used:

| Column | Used for |
|--------|----------|
| STUDENT NAME | Profile header, directory |
| FATHER'S NAME | Profile field |
| MOTHER'S NAME | Profile field |
| ADM NO | Admission number |
| DATE OF BIRTH | Profile field, age analytics |
| M/F | Gender analytics |
| CASTE | Caste analytics |
| RELIGION | Religion analytics |
| CORRESPONDENCE ADDRESS | Profile field |
| MOBILE (FATHER) | Mobile section |
| MOBILE NO (MOTHER) | Mobile section |
| SUBJECT OPTED | Subject analytics |
| EMAIL ID | Profile field |
| ADHAR NO | Profile field |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.10+, Flask |
| PDF Generation | ReportLab (canvas), pypdf (merge) |
| Data Processing | pandas, openpyxl |
| Frontend | HTML5, CSS3 (custom), Vanilla JS |
| Charts | Chart.js 4 |

---

## Output

- **Individual PDFs** → `output/individual/001_STUDENT_NAME.pdf`
- **Merged PDF** → `output/ALL_STUDENT_PROFILES.pdf`
- **One A4 page per student** replicating the official PM Shri KV profile format
