
import streamlit as st
from docx import Document
from docx.shared import Pt

def generate_report(data):
    doc = Document()
    style = doc.styles['Normal']
    style.font.name = 'Times New Roman'
    style.font.size = Pt(12)

    doc.add_paragraph(f"Name: {data['name']}")
    doc.add_paragraph(f"SSN (Last 4): {data['ssn']}")
    doc.add_paragraph(f"DOB: {data['dob']}")
    doc.add_paragraph(f"Date of Examination: {data['exam_date']}")
    doc.add_paragraph("")  # Blank line
    doc.add_paragraph(f"Chief Complaint: {data['chief_complaint']}")

    def section(title, body):
        para = doc.add_paragraph()
        run = para.add_run(title)
        run.bold = True
        doc.add_paragraph(body)

    section("History of Present Illness", data['hpi'])
    section("Past Medical History", data['pmh'])
    section("Social & Family History", data['social'] + "\n\n" + data['family'])
    section("Activities of Daily Living", data['adl'])
    section("Physical Examination", f"Vitals: {data['vitals']}\n\nFindings: {data['exam']}")
    section("Assessment & Functional Capacity", data['assessment'] + "\n\n" + data['capacity'])

    filename = f"{data['name'].replace(' ', '_')}_DDS_Report.docx"
    doc.save(filename)
    return filename

st.title("DDS Exam Report Builder")

data = {}
data['name'] = st.text_input("Full Name")
data['ssn'] = st.text_input("SSN (Last 4)")
import datetime
data['dob'] = st.date_input(
    "Date of Birth",
    min_value=datetime.date(1, 1, 1900),
    max_value=datetime.date.today()
)
data['exam_date'] = st.date_input("Date of Exam")
data['chief_complaint'] = st.text_area("Chief Complaint", help="Align with DDS if provided.")
data['hpi'] = st.text_area("History of Present Illness")
data['pmh'] = st.text_area("Past Medical History")
data['social'] = st.text_area("Social History")
data['family'] = st.text_area("Family History")
data['adl'] = st.text_area("Activities of Daily Living")
data['vitals'] = st.text_area("Vitals (BP, HR, Temp)")
data['exam'] = st.text_area("Exam Findings")
data['assessment'] = st.text_area("Assessment / Medical Impressions")
data['capacity'] = st.text_area("Functional Limitations")

for key in ['chief_complaint', 'hpi', 'pmh', 'adl', 'exam', 'assessment']:
    if data[key] and len(data[key]) < 30:
        st.warning(f"'{key.replace('_', ' ').title()}' appears brief — consider expanding.")

if st.button("Generate Word Document"):
    file = generate_report(data)
    with open(file, "rb") as f:
        st.download_button("Download DDS Report", f, file_name=file)
