"""
app.py — Vidyarthi Portal
Flask backend: serves the web UI, handles Excel uploads,
triggers PDF generation, and returns analytics as JSON.
"""

import os
import json
import uuid
from flask import (
    Flask, render_template, request,
    jsonify, send_file, abort
)
from werkzeug.utils import secure_filename

from analytics import compute_analytics
from generate_profiles import generate_all_profiles

# ── config ──────────────────────────────────
UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "output"
ALLOWED_EXTENSIONS = {"xlsx", "xls"}

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# In-memory store for last upload (single-user demo)
_state = {"excel_path": None, "merged_pdf": None}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# ── routes ──────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload():
    """Accept an Excel file, return analytics JSON."""
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "Only .xlsx / .xls files are accepted"}), 400

    filename = f"{uuid.uuid4().hex}_{secure_filename(file.filename)}"
    path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(path)

    try:
        analytics = compute_analytics(path)
        _state["excel_path"] = path
        _state["merged_pdf"] = None
        return jsonify({"success": True, "analytics": analytics})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/generate", methods=["POST"])
def generate():
    """Generate all student profile PDFs and merge them."""
    if not _state.get("excel_path"):
        return jsonify({"error": "Upload an Excel file first"}), 400

    try:
        session_out = os.path.join(OUTPUT_FOLDER, uuid.uuid4().hex)
        merged = generate_all_profiles(_state["excel_path"], output_dir=session_out)
        _state["merged_pdf"] = merged
        return jsonify({"success": True, "message": "PDF generated successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/download")
def download():
    """Serve the merged PDF for download."""
    pdf = _state.get("merged_pdf")
    if not pdf or not os.path.exists(pdf):
        abort(404)
    return send_file(
        pdf,
        as_attachment=True,
        download_name="ALL_STUDENT_PROFILES.pdf",
        mimetype="application/pdf",
    )


# ── run ─────────────────────────────────────
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "").lower() in {"1", "true", "yes"}
    app.run(host="0.0.0.0", port=port, debug=debug)
