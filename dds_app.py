import streamlit as st
import datetime
from openai import OpenAI
from docx import Document
from docx.shared import Pt

# Configuration: System prompt with detailed reporting guidelines
SYSTEM_PROMPT = st.secrets.get(
    "SYSTEM_PROMPT",
    """
You are an experienced disability examiner who writes Social Security Disability consultative exam reports following the exact DDS template:
- Use Times New Roman, 12 pt, black font
- Headers (e.g., 'History of Present Illness:') must be bold
- The header block (Name, SSN, DOB, Date of Exam) is single‑spaced, no extra spacing, followed by a blank line before Chief Complaint
- Chief Complaint line begins with 'Chief Complaint:' on the same line as its content
- Each report section (HPI, PMH, etc.) should be a clear professional paragraph
- Do not include extraneous commentary or unrelated text
"""
)

# Initialize OpenAI Client
client = OpenAI(api_key=st.secrets['OPENAI_API_KEY'])

# Function to call GPT with the detailed system prompt
def ai_generate(section_name, notes):
    # Combine system guidelines with section-specific instruction
    prompt = f"Write the '{section_name}' section based on these notes:\n{notes}"
    try:
        response = client.chat.completions.create(
            model='gpt-3.5-turbo',
            messages=[
                {'role': 'system', 'content': SYSTEM_PROMPT},
                {'role': 'user', 'content': prompt}
            ],
            temperature=0.2,
            max_tokens=300
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        # Handle rate limit or other API errors
        if hasattr(e, 'status') and e.status == 429:
            st.error('Rate limit exceeded. Please wait a moment and try again.')
        else:
            st.error(f"Error generating {section_name}: {e}")
        return ''

# Function to generate Word report
def generate_report(data):
    doc = Document()
    style = doc.styles['Normal']
    style.font.name = 'Times New Roman'
    style.font.size = Pt(12)

    # Header block: single-spaced
    for field in ['name','ssn','dob','exam_date']:
        label = field.replace('_', ' ').title()
        doc.add_paragraph(f"{label}: {data.get(field, '')}").paragraph_format.space_after = Pt(0)
    doc.add_paragraph('')  # blank line before chief complaint
    doc.add_paragraph(f"Chief Complaint: {data.get('chief_complaint', '')}")

    # Section helper
    def section(title, content):
        p = doc.add_paragraph()
        p.add_run(f"{title}:").bold = True
        doc.add_paragraph(content)

    # Add each main section
    section('History of Present Illness', data.get('hpi', ''))
    section('Past Medical History', data.get('pmh', ''))
    section('Social & Family History', f"{data.get('social', '')}\n\n{data.get('family', '')}")
    section('Activities of Daily Living', data.get('adl', ''))
    section('Physical Examination', f"Vitals: {data.get('vitals', '')}\n\nFindings: {data.get('exam', '')}")
    section('Assessment & Functional Capacity', f"{data.get('assessment', '')}\n\n{data.get('capacity', '')}")

    # Save file
    filename = f"{data.get('name', '').replace(' ', '_')}_DDS_Report.docx"
    doc.save(filename)
    return filename

# Streamlit UI
st.title('DDS Exam Report Builder with GPT Assistance')

# Define the sections and initiate session_state
sections = [
    ('hpi','History of Present Illness - Onset, diagnosis, treatment, medication, current status, pain severity, conditional items'),
    ('pmh','Past Medical History Notes - list of past medical history'),
    ('social','Social History - relationship status, living situation, children, employment status, support from family or friends, alcohol, tobacco or drug use'),
    ('family','Family History'),
    ('adl','Activities of Daily Living'),
    ('exam','Physical Exam Findings'),
    ('assessment','Assessment and Impressions'),
    ('capacity','Functional Functional Capacity')
]
for key, _ in sections:
    st.session_state.setdefault(f'{key}_notes', '')
    st.session_state.setdefault(key, '')

# Basic fields
data = {}
data['name'] = st.text_input('Full Name', key='input_name')
data['ssn'] = st.text_input('SSN (Last 4)', key='input_ssn')
data['dob'] = st.date_input('Date of Birth', min_value=datetime.date(1900,1,1), max_value=datetime.date.today(), key='input_dob')
data['exam_date'] = st.date_input('Date of Exam', key='input_exam_date')
data['chief_complaint'] = st.text_area('Chief Complaint - DDS provides CC in applicant file', key='input_cc')
data['vitals'] = st.text_area('Vitals - BP, Pulse, Height, Weight, Vision (corrected or non-corrected) Right - Left - Both', key='input_vitals')

# Notes and narrative for each section
for key, label in sections:
    notes_key = f'{key}_notes'
    narrative_key = key
    st.text_area(f'{label} Notes', value=st.session_state[notes_key], key=notes_key)
    if st.button(f'Draft {label}', key=f'btn_{key}'):
        st.session_state[narrative_key] = ai_generate(label, st.session_state[notes_key])
    data[key] = st.text_area(label, value=st.session_state[narrative_key], key=narrative_key)

# Generate and download report
if st.button('Generate Word Document'):
    file_path = generate_report(data)
    with open(file_path, 'rb') as f:
        st.download_button('Download DDS Report', f, file_name=file_path)
