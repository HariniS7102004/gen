import json

def build_cover_letter_prompt(data):
    user_keys = ["designation", "tools", "skills", "education", "experience_summary", "past_projects", "certifications","languages"]
    job_keys = ["job_title", "company", "link", "description", "responsibilities", "qualifications", "skills"]

    required_data = {
    "user_details": {k: data["user_details"][k] for k in user_keys if k in data["user_details"]},
    "job_description": {k: data["job_description"][k] for k in job_keys if k in data["job_description"]}
    }
    return f"""Generate a body within 150 words as 3 paragraphs for a formal cover letter using this data. Don't include the salutation or greetings. Don't include the skills explicitly. Don't include the heading as Cover Letter. Generate around 3 paragraphs for the body of the cover letter using the job description and user details, but don't include the company name.
Don't start all the sentences with I am.
Details:
{required_data}
Return only the formatted content as plain text for a .docx generation, but do NOT return any file or markdown."""

def build_resume_prompt(data):
    user_keys = ["designation", "tools", "skills", "experience_summary", "past_projects"]
    job_keys = ["job_title", "link", "description", "responsibilities", "qualifications", "skills"]

    required_data = {
    "user_details": {k: data["user_details"][k] for k in user_keys if k in data["user_details"]},
    "job_description": {k: data["job_description"][k] for k in job_keys if k in data["job_description"]}
    }
    return f"""Generate structured JSON content for a professional resume based on the following user details and job description. Do not include company names or fictional data. Don't include the word Resume in it. Give terms instead of sentences for skills and arrange them based on job requirement. Don't include any skills that is not present in user data.
Return past projects and experience summary data only if there is data for that in the input. Otherwise leave it blank.
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
  "past_projects": [
    {{
      "project_name": "..."
      "company_name": "...",
      "period": "...",
      "skills_used": "..."
      "description": "..."
    }},
    ...
  ],
  "skills": ["...", "..."]
}}

The description for each experience_summary and project must be atleast 70-80 words and the summary must be atleast 80 words relevant to the applying job. Ensure that each experience entry has a real company name (if provided in input), otherwise leave it blank. Make sure each field is properly filled based on the user input below. Do NOT return markdown or any additional explanation.

Details:
{required_data}"""

def translate_prompt(data, target_lang):
    return f"""
Translate the following JSON into {target_lang}. 
Only translate the values — do not change the keys or the JSON structure. 
Return the translated content as valid JSON in the same format.

{json.dumps(data, indent=2)}
"""