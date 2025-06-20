def build_cover_letter_prompt(data):
    user_keys = ["designation", "tools", "skills", "education", "experience_summary", "certifications","languages"]
    job_keys = ["job_title", "company", "responsibilities", "qualifications", "skills"]

    required_data = {
    "user_details": {k: data["user_details"][k] for k in user_keys if k in data["user_details"]},
    "job_description": {k: data["job_description"][k] for k in job_keys if k in data["job_description"]}
    }
    return f"""Generate a body within 150 words as 3 paragraphs for a formal cover letter using this data. Don't include the salutation or greetings. Don't include the skills explicitly. Don't include the heading as Cover Letter. Generate around 3 paragraphs for the body of the cover letter using the job description and user details, but don't include the company name.
Details:
{required_data}
Return only the formatted content as plain text for a .docx generation, but do NOT return any file or markdown."""

def build_resume_prompt(data):
    user_keys = ["designation", "tools", "skills", "experience_summary"]
    job_keys = ["job_title",  "responsibilities", "qualifications", "skills"]

    required_data = {
    "user_details": {k: data["user_details"][k] for k in user_keys if k in data["user_details"]},
    "job_description": {k: data["job_description"][k] for k in job_keys if k in data["job_description"]}
    }
    return f"""Generate structured JSON content for a professional resume based on the following user details and job description. Do not include company names or fictional data. Don't include the word Resume in it. Give terms instead of sentences for skills and arrange them based on job requirement.
Return a valid JSON with the following structure:
{{
  "summary": "...",
  "experience_summary": [
    {{
      "company_name": "...",
      "position": "...",
      "period": "...",
      "description": "..."
    }},
    ...
  ],
  "skills": ["...", "..."]
}}

The description for each experience_summary must be atleast 40-70 words and the summary must be atleast 60 words relevant to the applying job. Ensure that each experience entry has a real company name (if provided in input), otherwise leave it blank or realistic. Make sure each field is properly filled based on the input below. Do NOT return markdown or any additional explanation.

Details:
{required_data}"""