import requests
from bs4 import BeautifulSoup
import psycopg
import os
import time
import re
import urllib3
from datetime import datetime
from dotenv import load_dotenv

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
load_dotenv()

SKILLS = [
    "python", "sql", "machine learning", "deep learning", "tensorflow",
    "pytorch", "keras", "scikit-learn", "pandas", "numpy", "matplotlib",
    "nlp", "computer vision", "opencv", "tableau", "power bi",
    "spark", "hadoop", "aws", "azure", "gcp", "docker", "git",
    "r", "statistics", "data analysis", "neural networks", "llm",
    "langchain", "transformers", "huggingface", "mlflow", "airflow"
]

def get_connection():
    return psycopg.connect(os.getenv("DATABASE_URL"))

def extract_skills(text):
    text = text.lower()
    return [skill for skill in SKILLS if skill in text]

def parse_salary(salary_text):
    if not salary_text:
        return None, None
    numbers = re.findall(r'\d+\.?\d*', salary_text)
    if len(numbers) >= 2:
        return float(numbers[0]), float(numbers[1])
    elif len(numbers) == 1:
        return float(numbers[0]), float(numbers[0])
    return None, None

def save_job(conn, title, company, location, salary_text, job_url, description):
    cur = conn.cursor()
    salary_min, salary_max = parse_salary(salary_text)
    cur.execute("""
        INSERT INTO jobs (title, company, location, salary_min, salary_max, job_url, date_scraped)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (job_url) DO NOTHING
        RETURNING id
    """, (title, company, location, salary_min, salary_max, job_url, datetime.now()))
    result = cur.fetchone()
    if result:
        job_id = result[0]
        skills = extract_skills(description)
        for skill in skills:
            cur.execute("INSERT INTO job_skills (job_id, skill_name) VALUES (%s, %s)", (job_id, skill))
        print(f"  ✓ Saved: {title} at {company} | Skills: {skills[:5]}")
    else:
        print(f"  → Skipped (already in DB): {title} at {company}")
    conn.commit()
    cur.close()

def scrape_internshala(conn, search_term="machine learning"):
    print(f"\n📡 Scraping Internshala for '{search_term}'...")
    url = f"https://internshala.com/jobs/{search_term.replace(' ', '-')}-jobs"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        response = requests.get(url, headers=headers, timeout=10, verify=False)
        soup = BeautifulSoup(response.text, "html.parser")
        job_cards = soup.find_all("div", class_="individual_internship")
        if not job_cards:
            print("  No jobs found on Internshala")
            return
        for card in job_cards[:10]:
            try:
                title_el = card.find("h3", class_="job-internship-name")
                company_el = card.find("p", class_="company-name")
                location_el = card.find("p", class_="locations")
                salary_el = card.find("span", class_="stipend")
                link_el = card.find("a", class_="view_detail_button")
                title = title_el.text.strip() if title_el else "Unknown"
                company = company_el.text.strip() if company_el else "Unknown"
                location = location_el.text.strip() if location_el else "India"
                salary = salary_el.text.strip() if salary_el else ""
                job_url = "https://internshala.com" + link_el["href"] if link_el else url
                description = f"{title} {company} {search_term}"
                save_job(conn, title, company, location, salary, job_url, description)
                time.sleep(0.5)
            except Exception as e:
                print(f"  Error parsing card: {e}")
                continue
    except Exception as e:
        print(f"  Failed to scrape Internshala: {e}")

def scrape_remoteok(conn, search_term="machine-learning"):
    print(f"\n📡 Fetching RemoteOK API for '{search_term}'...")
    url = f"https://remoteok.com/api?tag={search_term}"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        jobs = response.json()
        jobs = [j for j in jobs if isinstance(j, dict) and "position" in j]
        if not jobs:
            print("  No jobs found")
            return
        for job in jobs[:10]:
            try:
                title = job.get("position", "Unknown")
                company = job.get("company", "Unknown")
                location = job.get("location", "Remote")
                tags = " ".join(job.get("tags", []))
                description = job.get("description", "") or ""
                description = BeautifulSoup(description, "html.parser").get_text()
                job_url = job.get("url", "https://remoteok.com")
                salary_min_raw = job.get("salary_min")
                salary_max_raw = job.get("salary_max")
                salary_text = f"{salary_min_raw}-{salary_max_raw}" if salary_min_raw and salary_max_raw else ""
                full_description = f"{title} {company} {tags} {description[:500]}"
                save_job(conn, title, company, location, salary_text, job_url, full_description)
                time.sleep(0.3)
            except Exception as e:
                print(f"  Error parsing job: {e}")
                continue
    except Exception as e:
        print(f"  Failed to fetch RemoteOK: {e}")

def run_scraper():
    print("🚀 Starting job scraper...")
    print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    conn = get_connection()

    for term in ["machine learning", "data science", "python developer"]:
        scrape_internshala(conn, term)
        time.sleep(2)

    for term in ["machine-learning", "data-science", "python"]:
        scrape_remoteok(conn, term)
        time.sleep(2)

    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM jobs")
    total_jobs = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM job_skills")
    total_skills = cur.fetchone()[0]
    cur.close()
    conn.close()

    print(f"\n✅ Scraping complete!")
    print(f"📊 Total jobs in DB: {total_jobs}")
    print(f"🔧 Total skills in DB: {total_skills}")

if __name__ == "__main__":
    run_scraper()