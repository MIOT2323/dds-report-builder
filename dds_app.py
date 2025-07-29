import streamlit as st
import datetime
from openai import OpenAI
from docx import Document
from docx.shared import Pt

# Initialize OpenAI Client
client = OpenAI(api_key=st.secrets['OPENAI_API_KEY'])

# Function to call GPT
def ai_generate(section_name, notes):
    prompt = f"""
You are an experienced disability examiner. Write a concise, professional paragraph for the '{section_name}' section of a DDS report based on the following notes:

{notes}
"""
    try:
        response = client.chat.completions.create(
            model='gpt-3.5-turbo',
            messages=[
                {'role': 'system', 'content': 'You write Social Security Disability consultative exam reports.'},
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
            st.error(f'Error generating {section_name}: {e}')
        return ''

# Generate Word report
def generate_report(data):
    doc = Document()
    style = doc.styles['Normal']
    style.font.name = 'Times New Roman'
    style.font.size = Pt(12)

    # Header
    for field in ['name','ssn','dob','exam_date']:
        doc.add_paragraph(f"{field.replace('_',' ').title()}: {data.get(field,'')}" )
    doc.add_paragraph('')
    doc.add_paragraph(f"Chief Complaint: {data.get('chief_complaint','')}" )

    # Sections
    def section(title, content):
        p = doc.add_paragraph()
        p.add_run(f"{title}:").bold = True
        doc.add_paragraph(content)

    section('History of Present Illness', data.get('hpi',''))
    section('Past Medical History', data.get('pmh',''))
    section('Social & Family History', f"{data.get('social','')}\n\n{data.get('family','')}")
    section('Activities of Daily Living', data.get('adl',''))
    section('Physical Examination', f"Vitals: {data.get('vitals','')}\n\nFindings: {data.get('exam','')}")
    section('Assessment & Functional Capacity', f"{data.get('assessment','')}\n\n{data.get('capacity','')}")

    filename = f"{data.get('name','').replace(' ','_')}_DDS_Report.docx"
    doc.save(filename)
    return filename

st.title('DDS Exam Report Builder with GPT Assistance')

# Define sections
sections = [
    ('hpi','History of Present Illness'),
    ('pmh','Past Medical History'),
    ('social','Social History'),
    ('family','Family History'),
    ('adl','Activities of Daily Living'),
    ('exam','Physical Exam Findings'),
    ('assessment','Assessment and Impressions'),
    ('capacity','Functional Capacity')
]

# Initialize state
for key,_ in sections:
    notes_key = f"{key}_notes"
    if notes_key not in st.session_state:
        st.session_state[notes_key] = ''
    if key not in st.session_state:
        st.session_state[key] = ''

# Input fields
data = {}
data['name'] = st.text_input('Full Name', key='input_name')
data['ssn'] = st.text_input('SSN (Last 4)', key='input_ssn')
data['dob'] = st.date_input('Date of Birth', min_value=datetime.date(1900,1,1), max_value=datetime.date.today(), key='input_dob')
data['exam_date'] = st.date_input('Date of Exam', key='input_exam_date')
data['chief_complaint'] = st.text_area('Chief Complaint', key='input_cc')

data['vitals'] = st.text_area('Vitals', key='input_vitals')

# Notes and narrative for each section
for key,label in sections:
    notes_key = f"{key}_notes"
    narrative_key = key

    st.text_area(f'{label} Notes', value=st.session_state[notes_key], key=notes_key)
    if st.button(f'Draft {label}', key=f'btn_{key}'):
        st.session_state[narrative_key] = ai_generate(label, st.session_state[notes_key])
    data[key] = st.text_area(label, value=st.session_state[narrative_key], key=narrative_key)

# Generate report
if st.button('Generate Word Document'):
    file = generate_report(data)
    with open(file,'rb') as f:
        st.download_button('Download DDS Report', f, file_name=file)
