import streamlit as st
import datetime
import openai
from docx import Document
from docx.shared import Pt

# Initialize OpenAI API key
openai.api_key = st.secrets["OPENAI_API_KEY"]

def ai_generate(section_name, notes):
    prompt = (
        f"You are an experienced disability examiner. Write a concise, professional "
        f"paragraph for the '{section_name}' section of a DDS report based on the following notes:\n\n{notes}"
    )
    response = openai.ChatCompletion.create(
        model="gpt-4",
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
data['hpi_notes'] = st.text_area("HPI Notes")
if st.button("Draft HPI"):
    data['hpi'] = ai_generate("History of Present Illness", data['hpi_notes'])
data['hpi'] = st.text_area("HPI Paragraph", value=data.get('hpi', ''))

data['pmh_notes'] = st.text_area("PMH Notes")
if st.button("Draft PMH"):
    data['pmh'] = ai_generate("Past Medical History", data['pmh_notes'])
data['pmh'] = st.text_area("Past Medical History", value=data.get('pmh', ''))

data['social_notes'] = st.text_area("Social History Notes")
if st.button("Draft Social History"):
    data['social'] = ai_generate("Social History", data['social_notes'])
data['social'] = st.text_area("Social History", value=data.get('social', ''))

data['family_notes'] = st.text_area("Family History Notes")
if st.button("Draft Family History"):
    data['family'] = ai_generate("Family History", data['family_notes'])
data['family'] = st.text_area("Family History", value=data.get('family', ''))

data['adl_notes'] = st.text_area("ADL Notes")
if st.button("Draft ADL"):
    data['adl'] = ai_generate("Activities of Daily Living", data['adl_notes'])
data['adl'] = st.text_area("Activities of Daily Living", value=data.get('adl', ''))

data['vitals'] = st.text_area("Vitals")
data['exam_notes'] = st.text_area("Exam Findings Notes")
if st.button("Draft Physical Exam"):
    data['exam'] = ai_generate("Physical Exam Findings", data['exam_notes'])
data['exam'] = st.text_area("Physical Exam Findings", value=data.get('exam', ''))

data['assessment_notes'] = st.text_area("Assessment Notes")
if st.button("Draft Assessment"):
    data['assessment'] = ai_generate("Assessment and Impressions", data['assessment_notes'])
data['assessment'] = st.text_area("Assessment", value=data.get('assessment', ''))

data['capacity_notes'] = st.text_area("Functional Capacity Notes")
if st.button("Draft Functional Capacity"):
    data['capacity'] = ai_generate("Functional Capacity", data['capacity_notes'])
data['capacity'] = st.text_area("Functional Capacity", value=data.get('capacity', ''))

if st.button("Generate Word Document"):
    file = generate_report(data)
    with open(file, "rb") as f:
        st.download_button("Download DDS Report", f, file_name=file)
