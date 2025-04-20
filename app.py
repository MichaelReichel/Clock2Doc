import os
from flask import Flask, request, send_file, render_template
import pandas as pd
from weasyprint import HTML
from datetime import datetime
from werkzeug.utils import secure_filename

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
INVOICE_FOLDER = "invoices"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(INVOICE_FOLDER, exist_ok=True)

@app.route("/")
def home():
    return render_template("homepage.html")

@app.route("/generate", methods=["POST"])
def generate_invoice():
    file = request.files.get("csv_file")
    if not file:
        return "No file uploaded", 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    # Load and process CSV
    try:
        df = pd.read_csv(filepath)
        if "Duration" in df.columns:
            df["Hours"] = pd.to_timedelta(df["Duration"]).dt.total_seconds() / 3600
        elif "Time (h)" in df.columns:
            df["Hours"] = pd.to_numeric(df["Time (h)"], errors="coerce")
        else:
            return "CSV missing expected duration column", 400

        total_hours = df["Hours"].sum()
        today = datetime.today().strftime('%Y-%m-%d')

        # Simple HTML for invoice (in a real app use a separate template file)
        html = f"""
        <h1>Invoice</h1>
        <p>Date: {today}</p>
        <p>Total Hours: {total_hours:.2f}</p>
        <p>Generated from Clockify CSV</p>
        """

        pdf_path = os.path.join(INVOICE_FOLDER, f"invoice_{today}.pdf")
        HTML(string=html).write_pdf(pdf_path)
        return send_file(pdf_path, as_attachment=True)

    except Exception as e:
        return f"Error generating invoice: {e}", 500

if __name__ == "__main__":
    app.run(debug=True)
