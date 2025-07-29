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
- Each report section should be a clear professional paragraph without extraneous commentary
"""
)
# Initialize OpenAI Client
client = OpenAI(api_key=st.secrets['OPENAI_API_KEY'])

def ai_generate(section_name, notes):
    """Call GPT to draft a section based on notes"""
    prompt = f"""
You are an experienced disability examiner. Write a concise, professional paragraph for the '{section_name}' section of a DDS report based on these notes:

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
            st.error('Rate limit exceeded. Please wait and try again.')
        else:
            st.error(f"Error generating {section_name}: {e}")
        return ''


def generate_report(data):
    """Generate the Word document based on collected data"""
    doc = Document()
    style = doc.styles['Normal']
    style.font.name = 'Times New Roman'
    style.font.size = Pt(12)
    # Header block
    for field in ['name', 'ssn', 'dob', 'exam_date']:
        label = field.replace('_', ' ').title()
        p = doc.add_paragraph(f"{label}: {data.get(field, '')}")
        p.paragraph_format.space_after = Pt(0)
    doc.add_paragraph('')
    doc.add_paragraph(f"Chief Complaint: {data.get('chief_complaint', '')}")
    # Helper for sections
    def section(title, content):
        p = doc.add_paragraph()
        p.add_run(f"{title}:").bold = True
        doc.add_paragraph(content)
    # Ordered sections
    section('History of Present Illness', data.get('hpi', ''))
    section('Past Medical History', data.get('pmh', ''))
    section('Family History', data.get('family', ''))
    section('Social History', data.get('social', ''))
    section('Review of Systems', data.get('ros', ''))
    section('Activities of Daily Living', data.get('adl', ''))
    # Physical Exam composite
    phys = (
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
    section('Physical Examination', phys)
    section('Neuro', data.get('neuro', ''))
    section('Skin', data.get('skin', ''))
    section('Assessment and Impressions', data.get('assessment', ''))
    section('Conclusion - Functional Ability', data.get('capacity', ''))
    # Save
    filename = f"{data.get('name', '').replace(' ', '_')}_DDS_Report.docx"
    doc.save(filename)
    return filename

# Streamlit UI
st.title('DDS Exam Report Builder with GPT Assistance')
# Input order
data = {}
data['name'] = st.text_input('Name')
data['ssn'] = st.text_input('SSN (Last 4)')
data['dob'] = st.date_input('Date of Birth', min_value=datetime.date(1900,1,1), max_value=datetime.date.today())
data['exam_date'] = st.date_input('Date of Exam')
data['chief_complaint'] = st.text_area('Chief Complaint - DDS provides CC in applicant file')
# Section notes and narratives
fields = [
    ('hpi', 'History of Present Illness'),
    ('pmh', 'Past Medical History'),
    ('family', 'Family History'),
    ('social', 'Social History'),
    ('ros', 'Review of Systems'),
    ('adl', 'Activities of Daily Living'),
]
# Initialize state
for key, _ in fields + [('neuro','Neuro'),('skin','Skin'),('assessment','Assessment and Impressions'),('capacity','Conclusion - Functional Ability')]:
    st.session_state.setdefault(f'{key}_notes', '')
    st.session_state.setdefault(key, '')
# Render notes & draft for initial sections
for key, label in fields:
    st.text_area(f'{label} Notes', key=f'{key}_notes')
    if st.button(f'Draft {label}', key=f'btn_{key}'):
        st.session_state[key] = ai_generate(label, st.session_state[f'{key}_notes'])
    data[key] = st.text_area(label, value=st.session_state[key], key=key)
# Physical Exam Inputs
st.subheader('Physical Examination Details')
data['general_observations'] = st.text_area('General Observations')
data['vitals'] = st.text_area('Vitals - BP, Pulse, Height, Weight, Vision (corrected or non-corrected) Right - Left - Both')
data['heent'] = st.text_area('HEENT')
data['respiratory'] = st.text_area('Respiratory')
data['cardiac'] = st.text_area('Cardiac')
data['digestive'] = st.text_area('Digestive')
data['upper_extremities'] = st.text_area('Upper Extremities')
data['lower_extremities'] = st.text_area('Lower Extremities')
data['spines'] = st.text_area('Cervical and Thoracic Spines')
# Remaining sections
remaining = [
    ('neuro','Neuro'),
    ('skin','Skin'),
    ('assessment','Assessment and Impressions'),
    ('capacity','Conclusion - Functional Ability')
]
for key, label in remaining:
    st.text_area(f'{label} Notes', key=f'{key}_notes')
    if st.button(f'Draft {label}', key=f'btn_{key}'):
        st.session_state[key] = ai_generate(label, st.session_state[f'{key}_notes'])
    data[key] = st.text_area(label, value=st.session_state[key], key=key)
# Generate report
if st.button('Generate Word Document'):
    file_path = generate_report(data)
    with open(file_path, 'rb') as f:
        st.download_button('Download DDS Report', f, file_name=file_path)
