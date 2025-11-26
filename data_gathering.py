import requests
import re
import pandas as pd
import sqlite3

from secrets import secrets
api_key = secrets['RAPIDAPI-KEY']
database_name = secrets['DB-NAME']

url = "https://jsearch.p.rapidapi.com/search"

# Specify data to get from the response
KEY_DATA = ['job_title', 'employer_name', 'employer_website', 'job_description', 'job_is_remote', 
            'job_publisher', 'job_apply_link', 'job_employment_type', 'job_employment_types', 
            'job_posted_at', 'job_city', 'job_min_salary', 'job_max_salary', 'job_salary_period']

TOOL_KEYWORDS = [
    "python", "sql", "excel", "tableau", "power bi", "r", "aws", "azure", "powerpoint",
    "spark", "java", "snowflake", "scala", "databricks", "git", "nosql", "oracle",
    "docker", "sql server", "kubernetes", "pyspark", "mongodb", "tensorflow", "sas",
    "sap", "shell", "go", "c++", "github", "linux", "word", "numpy", "terraform"]

SKILL_KEYWORDS = [
    "communication", "problem-solving", "analytical", "stakeholder management",
    "critical thinking", "mathematics", "statistics", "cleaning", "modeling",
    "data wrangling", "data cleaning", "data architecture", "story-telling"]
   
def extract_details(description):
    """
    Extracts job details from the job description.
    """
    desc_lower = description.lower()
    
    # 1. Tools
    found_tools = []
    for tool in TOOL_KEYWORDS:
        pattern = r'\b' + re.escape(tool) + r'\b'
        if re.search(pattern, desc_lower):
            found_tools.append(tool)

    # 2. Skills
    found_skills = []
    for skill in SKILL_KEYWORDS:
        pattern = r'\b' + re.escape(skill) + r'\b'
        if re.search(pattern, desc_lower):
            found_skills.append(skill.strip())
    
    # 3. Experience
    # look for years/yrs
    experience_pattern = r'(\d+|one|two|three|four|five)\+?\s*(?:-\s*\d+)?\s*(?:years?|yrs?)'
    experience_match = None
    experience_match = re.search(experience_pattern, description)
    if experience_match:
        experience = experience_match.group(0)
    else:
        if "graduate" in desc_lower: experience = "Graduate/Entry Level required."
        elif "entry level" in desc_lower: experience = "Entry Level required."
        elif "internship" in desc_lower: experience = "Internship experience relevant."
        else: experience = None
        
    # 4. Salary
    # look for £ followed by numbers, optional 'k', optional range
    salary_pattern = r'£[\d,]+(?:k)?(?:\s*-\s*£[\d,]+(?:k)?)?'
    salary_match = re.search(salary_pattern, description)
    salary = salary_match.group(0) if salary_match else "Not listed"

    # 5. Contract Type
    contract_type = "Permanent"
    if "fixed term" in desc_lower or "ftc" in desc_lower or "contract" in desc_lower:
        contract_type = "Fixed Term/Contract"
    elif "internship" in desc_lower or "placement" in desc_lower:
        contract_type = "Internship"
    elif "part-time" in desc_lower:
        contract_type = "Part-Time"

    # 6. Start Date
    # look for "Start Date" followed by some text
    start_date_match = re.search(r'Start Date\s*:?\s*(.*?)(\n|$)', description, re.IGNORECASE)
    start_date = start_date_match.group(1) if start_date_match else "ASAP"

    return {
        "tools": ", ".join(found_tools),
        "skills": ", ".join(found_skills),
        "experience": experience,
        "salary": salary,
        "contract": contract_type,
        "start_date": start_date
    }

if __name__ == "__main__":

    # construct query
    querystring = {"query":"junior data analyst in london","page":"1","num_pages":"50","country":"gb","date_posted":"all"}
    headers = {
        "x-rapidapi-key": api_key,
        "x-rapidapi-host": "jsearch.p.rapidapi.com"
    }
    response = requests.get(url, headers=headers, params=querystring)
    data = response.json()['data']

    # extract job data from response data
    job_data = []
    for job in data:
        jd = {}
        for data_key in KEY_DATA:
            jd[data_key] = job[data_key]
        for key, val in extract_details(job['job_description']).items():
            jd[key] = val
        job_data.append(jd)


    # convert lists to strings before saving
    df = pd.DataFrame(job_data)
    df_clean = df.copy()
    print("DTypes: " + df_clean.dtypes)
    for col in df_clean.columns:
        # if col type is <list>, convert to <str>
        if df_clean[col].apply(lambda x: isinstance(x, list)).any():
            df_clean[col] = df_clean[col].astype(str)

    # save to SQL
    conn = sqlite3.connect(F'{database_name}.db')
    df_clean.to_sql('jobs', conn, if_exists='append', index=False)
    conn.close()
    print(f"Appended jobs to {database_name}.db")