import json
import os

import streamlit as st
from docx import Document
from dotenv import load_dotenv
from pypdf import PdfReader

load_dotenv()

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL")
MODEL = os.getenv("OLLAMA_MODEL")

REPORT_SECTION = [
    ("strenghts","Strenghts"),
    ("gaps","Gaps"),
    ("missing_or_weak_skills","Missing or Weak Skills"),
    ("improvement_suggestions","Improvement Suggestions"),
    ("overall_summary","Overall Summary"),
]

def extract_resume_text(uploaded_file):
    file_name = uploaded_file.name.lower()

    if file_name.endswith(".pdf"):
        reader = pdfReader(uploaded_file)
        pages = []
        for page in reader.pages:
            pages.append(page.extract_text() or "")
        return "\n".join(pages).strip()

    if file_name.endswith(".docx"):
        document = Document(uploaded_file)
        paragraphs = []
        for paragraphs in document.paragraph:
            paragraphs.append(paragraphs.txt)
        return "\n".join(paragraphs).strip()

    return ""

    def analyze_resume(resume_text,job_description):
        client = OpenAI(api_key=API_KEY)

        instructions = """You compare resumes against job descriptions.

Reply with JSON only, using exactly these keys. Every value is a list of short strings.

{
  "candidate_skills": [],
  "candidate_experience": [],
  "candidate_qualifications": [],
  "required_skills": [],
  "preferred_skills": [],
  "matching_skills": [],
  "missing_skills": [],
  "gaps": []
}

Rules:
- Use only information that actually appears in the resume or the job description.
- Never invent skills, employers, job titles, dates, certifications or achievements.
- "missing_skills" means the job description asks for it and the resume does not mention it.
- Leave a list empty when the text gives you nothing to put in it.
"""

    # The word "JSON" has to appear in the input below, not only in the
    # instructions above, or the API rejects the json_object format.
    user_message = f"""Compare this resume against this job description and reply with JSON.

RESUME:
{resume_text}

JOB DESCRIPTION:
{job_description}
"""
    response = client.responses.create(
        model= MODEL,
        instructions=instructions,
        input=user_message,
        text={"format":{"type":"json_object"}},
    )                


    return json.loads(response.output_text)

def generate_final_report(structured_analysis):
    client =OLLAMA(ollama_base_url=OLLAMA_BASE_URL)

    instructions = """You write short, honest resume feedback for a candidate.

You receive JSON that was built from a resume and a job description.
Reply with JSON only, using exactly these keys. Every value is a string.

{
  "strengths": "",
  "gaps": "",
  "missing_or_weak_skills": "",
  "improvement_suggestions": "",
  "overall_summary": ""
}

Rules:
- Write the first four values as Markdown bullet lists, one point per line ("- point").
- Write "overall_summary" as one short paragraph.
- Never leave a value empty. If a section has nothing to report, say so in one bullet,
  such as "- Nothing further was identified from the provided resume."
- Put specific tools and technologies in "missing_or_weak_skills", and put experience,
  qualifications and responsibilities in "gaps", so the two do not repeat each other.
- Base everything on the JSON you are given, and do not invent anything new.
- Never use the words "lacks", "lacking", "no experience", "no exposure",
  "does not know" or "does not have" anywhere, including the overall summary.
  You only know what this one resume mentions, not what the candidate can really do.
  Write "Apache Airflow was not identified in the provided resume" and
  "The resume does not show the 3+ years of analytics experience the role asks for".
- Do not give a numeric score or a percentage.
"""

    # The output of the first call becomes the input of the second call.
    # The word "JSON" has to appear here too, for the same reason as above.
    user_message = f"""Turn this structured data into resume feedback and reply with JSON.

{json.dumps(structured_analysis, indent=2)}
"""
    response = client.responses.create(
        model=MODEL,
        instructions=instructions,
        input=user_message,
        text={"format":{"type":"json_object"}},
    )

    report = json.loads(response.output_text)

    for key,_ in REPORT_SECTIONS:
        value = report.get(key)
        if isinstance(value,list):
            value = "\n".join("- " + str(point) for point in value)
        report[key] = value or "Nothing was reported for this section."

    return report

def create_downloadable_report(final_report):
    lines=["# RESUME ANALYSIS"]
    for key,heading in REPORT_SECTIONS:
        lines.append("## " + heading)
        lines.append(final_report[key])
    return "\n\n".join(lines)
    
        
       