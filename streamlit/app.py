import streamlit as st
import pandas as pd
import requests
from PIL import Image
from fpdf import FPDF
import os
import io
import zipfile
from datetime import datetime
import tempfile

LLM_API_URL = "http://llm-service:5000/generate"

st.title("📄 Automated Hiring Letter Generator")
st.markdown("Upload employee data and a background letterhead image to generate personalized hiring letters.")

uploaded_csv = st.file_uploader("Upload CSV or Excel File", type=["csv", "xlsx"])
uploaded_image = st.file_uploader("Upload Background Image (JPG/PNG)", type=["jpg", "png"])

if uploaded_csv and uploaded_image:
    file_type = uploaded_csv.name.split(".")[-1].lower()
    df = pd.read_csv(uploaded_csv) if file_type == "csv" else pd.read_excel(uploaded_csv)

    required_cols = [
        "Full Name", "Role", "Hiring Date", "Reason for Hiring / Skills",
        "Responsibilities",  # optional, but keep it in CSV
        "Sender Name", "Company Name", "Sender Position"
    ]

    if not all(col in df.columns for col in required_cols):
        st.error(f"File must contain: {', '.join(required_cols)}")

    else:
        if st.button("Generate Letters"):
            st.info("Generating letters...")
            image = Image.open(uploaded_image).convert("RGB")

            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
                image.save(tmp_file, format="JPEG")
                tmp_file_path = tmp_file.name

            pdfs = []

            for _, row in df.iterrows():
                name = row["Full Name"]
                role = row["Role"]
                date = row["Hiring Date"]
                reason = row["Reason for Hiring / Skills"]
                responsibilities = row.get("Responsibilities", "")
                sender_name = row.get("Sender Name", "")
                company_name = row.get("Company Name", "")
                sender_position = row.get("Sender Position", "")

                try:
                    response = requests.post(LLM_API_URL, json={
                        "name": name,
                        "role": role,
                        "date": str(date),
                        "reason": reason,
                        "responsibilities": responsibilities,
                        "sender_name": sender_name,
                        "company_name": company_name,
                        "sender_position": sender_position
                    })
                    letter_text = response.json().get("text", "")
                except Exception as e:
                    st.error(f"Error generating letter for {name}: {e}")
                    continue

                pdf = FPDF()
                pdf.add_page()
                pdf.image(tmp_file_path, x=0, y=0, w=210, h=297)
                pdf.set_font("Arial", size=8)
                pdf.set_xy(10, 60)
                for line in letter_text.split("\n"):
                    pdf.multi_cell(0, 5, line.strip())  # reduced line spacing from 10 to 7

                output_filename = f"/tmp/{name.replace(' ', '_')}.pdf"
                pdf.output(output_filename)
                pdfs.append(output_filename)

            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w") as zip_file:
                for file_path in pdfs:
                    zip_file.write(file_path, os.path.basename(file_path))
            zip_buffer.seek(0)

            st.success("✅ Letters generated!")
            st.download_button(
                label="📥 Download All Letters (ZIP)",
                data=zip_buffer,
                file_name=f"letters_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
                mime="application/zip"
            )
