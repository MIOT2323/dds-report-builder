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
    prompt = f"""
You are an experienced disability examiner. Write a concise, professional paragraph for the '{section_name}' section of a DDS report based on the following notes:

{notes}
"""
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

    section('History of Present Illness', data.get('hpi', ''))
    section('Past Medical History', data.get('pmh', ''))
    section('Social & Family History', f"{data.get('social', '')}\n\n{data.get('family', '')}")
    section('Activities of Daily Living', data.get('adl', ''))

    # Physical Examination assembled from subfields
    phys_content = (
        f"General Observations: {data.get('general_observations', '')}\n\n"
        f"Vitals: {data.get('vitals', '')}\n\n"
        f"HEENT: {data.get('heent', '')}\n\n"
        f"Respiratory: {data.get('respiratory', '')}\n\n"
        f"Cardiac: {data.get('cardiac', '')}\n\n"
        f"Digestive: {data.get('digestive', '')}\n\n"
        f"Upper Extremities: {data.get('upper_extremities', '')}\n\n"
        f"Lower Extremities: {data.get('lower_extremities', '')}\n\n"
        f"Cervical and Thoracic Spines: {data.get('spines', '')}"
    )
    section('Physical Examination', phys_content)
    section('Assessment & Functional Capacity', f"{data.get('assessment', '')}\n\n{data.get('capacity', '')}")

    # Save file
    filename = f"{data.get('name', '').replace(' ', '_')}_DDS_Report.docx"
    doc.save(filename)
    return filename

# Streamlit UI
st.title('DDS Exam Report Builder with GPT Assistance')

# Define the sections and session state for notes and narratives
sections = [
    ('hpi','History of Present Illness - Onset, diagnosis, treatment, medication, current status, pain severity, conditional items'),
    ('pmh','Past Medical History Notes - list of past medical history'),
    ('social','Social History - relationship status, living situation, children, employment status, support from family or friends, alcohol, tobacco or drug use'),
    ('family','Family History - List of conditions known to run in family'),
    ('adl','Activities of Daily Living - Wake up, Bed Time, Chores, Daily Life'),
    ('exam','Physical Exam Findings - break down below'),
    ('assessment','Assessment and Impressions'),
    ('capacity','Functional Capacity')
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

# Activities of Daily Living
data['adl'] = st.text_area('Activities of Daily Living - Wake up, Bed Time, Chores, Daily Life', key='adl_notes')
# Physical Exam subfields
st.subheader('Physical Examination Details')
data['general_observations'] = st.text_area('General Observations', key='gen_obs')
data['vitals'] = st.text_area('Vitals - BP, Pulse, Height, Weight, Vision (corrected or non-corrected) Right - Left - Both', key='input_vitals')
data['heent'] = st.text_area('HEENT', key='heent_notes')
data['respiratory'] = st.text_area('Respiratory', key='respiratory_notes')
data['cardiac'] = st.text_area('Cardiac', key='cardiac_notes')
data['digestive'] = st.text_area('Digestive', key='digestive_notes')
data['upper_extremities'] = st.text_area('Upper Extremities', key='upper_ext_notes')
data['lower_extremities'] = st.text_area('Lower Extremities', key='lower_ext_notes')
data['spines'] = st.text_area('Cervical and Thoracic Spines', key='spines_notes')

# Notes and narrative for each remaining section
for key, label in [('hpi', 'History of Present Illness'), ('pmh', 'Past Medical History'), ('social', 'Social History'), ('family', 'Family History'), ('assessment', 'Assessment and Impressions'), ('capacity', 'Functional Capacity')]:
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
