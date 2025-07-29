import streamlit as st
import datetime
from openai import OpenAI
import openai
from docx import Document
from docx.shared import Pt

# Initialize OpenAI Client
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

def ai_generate(section_name, notes):
    prompt = (
        f"You are an experienced disability examiner. Write a concise, professional "
        f"paragraph for the '{section_name}' section of a DDS report based on the following notes:\n\n{notes}"
    )
    try:
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
    except openai.error.RateLimitError:
        st.error("Rate limit exceeded. Please wait a moment and try again.")
        return ""


def generate_report(data):
    doc = Document()
    style = doc.styles['Normal']
    style.font.name = 'Times New Roman'
    style.font.size = Pt(12)

    # Header
    doc.add_paragraph(f"Name: {data['name']}")
    doc.add_paragraph(f"SSN (Last 4): {data['ssn']}")
    doc.add_paragraph(f"DOB: {data['dob']}")
    doc.add_paragraph(f"Date of Examination: {data['exam_date']}")
    doc.add_paragraph("")
    doc.add_paragraph(f"Chief Complaint: {data['chief_complaint']}")

    # Sections
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

# App Title
st.title("DDS Exam Report Builder with GPT Assistance")

# Input fields
data = {}
data['name'] = st.text_input("Full Name")
data['ssn'] = st.text_input("SSN (Last 4)")
data['dob'] = st.date_input(
    "Date of Birth",
    min_value=datetime.date(1900, 1, 1),
    max_value=datetime.date.today()
)
data['exam_date'] = st.date_input("Date of Exam")
data['chief_complaint'] = st.text_area("Chief Complaint")

# Notes and GPT generation for each section
sections = [
    ("hpi", "History of Present Illness"),
    ("pmh", "Past Medical History"),
    ("social", "Social History"),
    ("family", "Family History"),
    ("adl", "Activities of Daily Living"),
    ("exam", "Physical Exam Findings"),
    ("assessment", "Assessment and Impressions"),
    ("capacity", "Functional Capacity")
]

for key, label in sections:
    notes_key = key + '_notes'
    data[notes_key] = st.text_area(f"{label} Notes")
    if st.button(f"Draft {label}"):
        data[key] = ai_generate(label, data[notes_key])
    data[key] = st.text_area(label, value=data.get(key, ''))

# Vitals
data['vitals'] = st.text_area("Vitals")

# Generate report
if st.button("Generate Word Document"):
    file = generate_report(data)
    with open(file, "rb") as f:
        st.download_button("Download DDS Report", f, file_name=file)
