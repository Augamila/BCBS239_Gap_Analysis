
import streamlit as st
import pandas as pd
from sentence_transformers import SentenceTransformer, util
from io import BytesIO
import pdfminer.high_level as pdfminer
import fitz  # PyMuPDF
import plotly.express as px
from report_generator import generate_pdf_report
from datetime import datetime

@st.cache_resource
def load_model():
    return SentenceTransformer('all-MiniLM-L6-v2')

model = load_model()

principles = {
    "Principle 1": "Governance - Data aggregation should be governed by strong risk data architecture.",
    "Principle 2": "Data architecture and IT infrastructure - Ensure flexibility and scalability for risk data.",
    "Principle 3": "Accuracy and Integrity - Risk data should be accurate and reliable.",
    "Principle 4": "Completeness - Risk data should be complete, capturing all relevant risk.",
    "Principle 5": "Timeliness - Risk data should be available when needed.",
    "Principle 6": "Adaptability - Risk data aggregation capabilities should be adaptable.",
    "Principle 7": "Accuracy of Reporting - Reports should reflect the nature of the risk.",
    "Principle 8": "Comprehensiveness - Reports should cover all material risk areas.",
    "Principle 9": "Clarity and Usefulness - Reports should be clear and useful to decision-makers.",
    "Principle 10": "Frequency - Risk reports should be produced as frequently as needed.",
    "Principle 11": "Distribution - Reports should reach all relevant parties.",
    "Principle 12": "Review - Capabilities should be reviewed regularly.",
    "Principle 13": "Remediation - Issues should be addressed promptly.",
    "Principle 14": "Supervision - Supervisors should be able to assess compliance."
}

def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    try:
        return pdfminer.extract_text(BytesIO(pdf_bytes))
    except Exception:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        text = "".join(page.get_text() for page in doc)
        doc.close()
        return text

def analyze_gaps(text: str) -> pd.DataFrame:
    enc_doc = model.encode(text)
    data = []
    for name, desc in principles.items():
        score = util.cos_sim(enc_doc, model.encode(desc)).item()
        status = (
            "✅ Compliant" if score > 0.75 else
            "⚠️ Partial" if score > 0.5 else
            "❌ Non‑Compliant"
        )
        data.append({
            "Principle": name,
            "Description": desc,
            "Score": round(score, 2),
            "Status": status,
            "Feedback": ""
        })
    return pd.DataFrame(data)

def calculate_score(df):
    def score_row(status):
        return 1.0 if "Compliant" in status else 0.5 if "Partial" in status else 0.0
    return round(df["Status"].apply(score_row).mean() * 100, 2)

def main():
    st.title("🧠 BCBS239 Gap Analysis Tool")
    st.markdown("Upload a policy PDF and compare it against BCBS239 principles.")

    org_name = st.text_input("🏢 Organization Name", value="")
    uploaded = st.file_uploader("📄 Upload PDF Document", type=['pdf'])

    if uploaded:
        doc_bytes = uploaded.read()
        with st.spinner("🔍 Extracting text..."):
            text = extract_text_from_pdf(doc_bytes)

        if not text.strip():
            st.error("❌ No text could be extracted.")
            return

        df = analyze_gaps(text)
        st.subheader("📊 Gap Analysis Results")
        df_edit = st.experimental_data_editor(df, num_rows="dynamic")
        st.caption("✏️ You can add feedback for each principle.")

        score = calculate_score(df_edit)
        st.metric(label="✅ Compliance Score", value=f"{score}%", delta=None)

        fig = px.bar(df_edit, x="Principle", y="Score", color="Status",
                     color_discrete_map={
                         "✅ Compliant": "green",
                         "⚠️ Partial": "orange",
                         "❌ Non‑Compliant": "red"
                     })
        fig.update_layout(xaxis_tickangle=-45, height=400)
        st.plotly_chart(fig, use_container_width=True)

        csv = df_edit.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Download CSV", csv, "bcbs239_gap_report.csv", "text/csv")

        if st.button("📄 Export as PDF"):
            pdf_bytes = generate_pdf_report(org_name, df_edit, score)
            st.download_button("⬇️ Download PDF Report", data=pdf_bytes, file_name="bcbs239_gap_report.pdf", mime="application/pdf")

if __name__ == "__main__":
    main()
