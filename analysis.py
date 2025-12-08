import sqlite3
import pandas as pd

from usr_secrets import secrets
database_name = secrets['DB-NAME']

# --- DATA --- #
def connect():
    conn = sqlite3.connect(f'{database_name}.db')
    return conn

def get_jobs():
    query = """
    SELECT *
    FROM jobs
    """
    conn = connect()
    df = pd.read_sql(query, conn)
    conn.close()

    return df

# --- FILTERS --- #
def is_junior(job):
    title = str(job.get('job_title', '')).lower()
    return 'junior' in title
    
def tools_filter(job, tools_filter: list[str]):

    # convert 'tools' cell from str -> list[str]
    job_tools = [job.strip() for job in job['tools'].split(',')]
    # Is every item in tools_filter, in job_tools?
    return all(item in job_tools for item in tools_filter)


output_file = "jobs_found"
if __name__ == "__main__":

    df = get_jobs()

    tools = ['sql', 'python']

    print("----- Jobs Found -----")
    jobs = {}
    for i, row in df.iterrows():
        if is_junior(row) and tools_filter(row, tools):
            title = row['job_title']
            link = row['job_apply_link']
            posted = row['job_posted_at']
            city = row['job_city']
            jobs[title] = {'link': link, 'posted': posted, 'city': city}

    print(f"Found {len(jobs)} jobs.")

    with open(f"{output_file}.md", "w") as f:
        for title, details in jobs.items():
            f.write(f"[{title}]({details['link']}) - {details['posted']} - {details['city']}\n\n")

    print(f"Write jobs to {output_file}.md")
    print("------ Finished ------")




