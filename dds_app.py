import streamlit as st
import datetime
from openai import OpenAI
from docx import Document
from docx.shared import Pt

# Initialize OpenAI Client
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

def ai_generate(section_name, notes):
    prompt = (
        f"You are an experienced disability examiner. Write a concise, professional "
        f"paragraph for the '{section_name}' section of a DDS report based on the following notes:\n\n{notes}"
    )
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You write Social Security Disability consultative exam reports."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2,
        max_tokens=300
    )
    return response.choices[0].message.content.strip()

def generate_report(data):
    doc = Document()
    style = doc.styles['Normal']
    style.font.name = 'Times New Roman'
    style.font.size = Pt(12)

    doc.add_paragraph(f"Name: {data['name']}")
    doc.add_paragraph(f"SSN (Last 4): {data['ssn']}")
    doc.add_paragraph(f"DOB: {data['dob']}")
    doc.add_paragraph(f"Date of Examination: {data['exam_date']}")
    doc.add_paragraph("")
    doc.add_paragraph(f"Chief Complaint: {data['chief_complaint']}")

    def section(title, content):
        para = doc.add_paragraph()
        run = para.add_run(title)
        run.bold = True
        doc.add_paragraph(content)

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

# Input fields
data = {}
data['name'] = st.text_input("Full Name")
data['ssn'] = st.text_input("SSN (Last 4)")
data['dob'] = st.date_input("Date of Birth", min_value=datetime.date(1900, 1, 1), max_value=datetime.date.today())
data['exam_date'] = st.date_input("Date of Exam")
data['chief_complaint'] = st.text_area("Chief Complaint")

# Notes and GPT generation for each major section
for section_key, section_label in [
    ("hpi", "History of Present Illness"),
    ("pmh", "Past Medical History"),
    ("social", "Social History"),
    ("family", "Family History"),
    ("adl", "Activities of Daily Living"),
    ("exam", "Physical Exam Findings"),
    ("assessment", "Assessment and Impressions"),
    ("capacity", "Functional Capacity")
]:
    notes_key = section_key + '_notes'
    data[notes_key] = st.text_area(f"{section_label} Notes")
    if st.button(f"Draft {section_label}"):
        data[section_key] = ai_generate(section_label, data[notes_key])
    data[section_key] = st.text_area(section_label, value=data.get(section_key, ''))

# Vitals
data['vitals'] = st.text_area("Vitals")

# Report Generation
if st.button("Generate Word Document"):
    file = generate_report(data)
    with open(file, "rb") as f:
        st.download_button("Download DDS Report", f, file_name=file)
