from rapidfuzz import fuzz

def filter_skills(output_json, user_data, job_data, min_similarity=50, max_additional=5):
    """
    Filters hallucinated skills and adds some additional relevant user skills based on fuzzy match with job description.

    Args:
        output_json (dict): Model-generated resume JSON.
        user_data (dict): Input user data with 'skills' and 'tools'.
        job_data (dict): Job description with 'skills', 'responsibilities', or 'qualifications'.
        min_similarity (int): Minimum fuzzy match score to consider a user skill as relevant.
        max_additional (int): Max number of extra relevant skills to add.

    Returns:
        dict: Cleaned and enhanced output.
    """
    user_skills = user_data.get("skills", [])
    user_tools = user_data.get("tools", [])
    all_user_terms = set(map(str.lower, user_skills + user_tools))
    
    # Keep only skills that match exactly with user data
    model_skills = output_json.get("skills", [])
    retained_skills = [
        skill for skill in model_skills if skill.lower() in all_user_terms
    ]

    # Extract job keywords
    job_keywords = (
        job_data.get("skills", []) +
        job_data.get("responsibilities", []) +
        job_data.get("qualifications", [])
    )
    job_keywords_flat = ' '.join(job_keywords).lower()

    # Identify additional user skills that are relevant to the job
    extra_skills = []
    for skill in user_skills + user_tools:
        score = fuzz.partial_ratio(skill.lower(), job_keywords_flat)
        if score >= min_similarity and skill not in retained_skills:
            extra_skills.append((skill, score))

    # Sort by relevance score and add top N
    extra_skills = sorted(extra_skills, key=lambda x: -x[1])[:max_additional]
    boosted_skills = retained_skills + [s[0] for s in extra_skills]

    output_json["skills"] = boosted_skills
    return output_json
