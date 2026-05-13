from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Job Market Intelligence API", version="1.0")

# ── Allow React frontend to talk to this API ──────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Database connection ───────────────────────────────────────────────────────
def get_conn():
    return psycopg2.connect(os.getenv("DATABASE_URL"))

# ── 1. Health check — is the API alive? ───────────────────────────────────────
@app.get("/")
def root():
    return {"message": "Job Market Intelligence API is running!"}

# ── 2. Total stats ────────────────────────────────────────────────────────────
@app.get("/stats")
def get_stats():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM jobs")
    total_jobs = cur.fetchone()[0]

    cur.execute("SELECT COUNT(DISTINCT company) FROM jobs")
    total_companies = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM job_skills")
    total_skills = cur.fetchone()[0]

    cur.execute("SELECT COUNT(DISTINCT skill_name) FROM job_skills")
    unique_skills = cur.fetchone()[0]

    cur.close()
    conn.close()

    return {
        "total_jobs": total_jobs,
        "total_companies": total_companies,
        "total_skill_mentions": total_skills,
        "unique_skills": unique_skills
    }

# ── 3. Trending skills ────────────────────────────────────────────────────────
@app.get("/skills/trending")
def trending_skills(limit: int = 15):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT skill_name, COUNT(*) as count
        FROM job_skills
        GROUP BY skill_name
        ORDER BY count DESC
        LIMIT %s
    """, (limit,))

    rows = cur.fetchall()
    cur.close()
    conn.close()

    return [{"skill": row[0], "count": row[1]} for row in rows]

# ── 4. Top hiring companies ───────────────────────────────────────────────────
@app.get("/companies/hiring")
def top_companies(limit: int = 10):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT company, COUNT(*) as job_count
        FROM jobs
        WHERE company != 'Unknown'
        GROUP BY company
        ORDER BY job_count DESC
        LIMIT %s
    """, (limit,))

    rows = cur.fetchall()
    cur.close()
    conn.close()

    return [{"company": row[0], "job_count": row[1]} for row in rows]

# ── 5. Jobs by location ───────────────────────────────────────────────────────
@app.get("/jobs/by-location")
def jobs_by_location():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT location, COUNT(*) as count
        FROM jobs
        WHERE location IS NOT NULL
        GROUP BY location
        ORDER BY count DESC
        LIMIT 10
    """)

    rows = cur.fetchall()
    cur.close()
    conn.close()

    return [{"location": row[0], "count": row[1]} for row in rows]

# ── 6. Salary stats ───────────────────────────────────────────────────────────
@app.get("/salary/stats")
def salary_stats():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            ROUND(AVG(salary_min)::numeric, 2) as avg_min,
            ROUND(AVG(salary_max)::numeric, 2) as avg_max,
            ROUND(MIN(salary_min)::numeric, 2) as lowest,
            ROUND(MAX(salary_max)::numeric, 2) as highest
        FROM jobs
        WHERE salary_min IS NOT NULL AND salary_max IS NOT NULL
    """)

    row = cur.fetchone()
    cur.close()
    conn.close()

    if row[0] is None:
        return {"message": "No salary data available yet"}

    return {
        "avg_min_lpa": float(row[0]),
        "avg_max_lpa": float(row[1]),
        "lowest_lpa": float(row[2]),
        "highest_lpa": float(row[3])
    }

# ── 7. Latest jobs feed ───────────────────────────────────────────────────────
@app.get("/jobs/latest")
def latest_jobs(limit: int = 20):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT j.id, j.title, j.company, j.location,
               j.salary_min, j.salary_max, j.job_url, j.date_scraped,
               ARRAY_AGG(js.skill_name) as skills
        FROM jobs j
        LEFT JOIN job_skills js ON j.id = js.job_id
        GROUP BY j.id, j.title, j.company, j.location,
                 j.salary_min, j.salary_max, j.job_url, j.date_scraped
        ORDER BY j.date_scraped DESC
        LIMIT %s
    """, (limit,))

    rows = cur.fetchall()
    cur.close()
    conn.close()

    return [{
        "id": row[0],
        "title": row[1],
        "company": row[2],
        "location": row[3],
        "salary_min": row[4],
        "salary_max": row[5],
        "job_url": row[6],
        "date_scraped": str(row[7]),
        "skills": [s for s in row[8] if s] if row[8] else []
    } for row in rows]

# ── 8. Search jobs ────────────────────────────────────────────────────────────
@app.get("/jobs/search")
def search_jobs(q: str, limit: int = 10):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT title, company, location, job_url, date_scraped
        FROM jobs
        WHERE LOWER(title) LIKE %s OR LOWER(company) LIKE %s
        ORDER BY date_scraped DESC
        LIMIT %s
    """, (f"%{q.lower()}%", f"%{q.lower()}%", limit))

    rows = cur.fetchall()
    cur.close()
    conn.close()

    return [{
        "title": row[0],
        "company": row[1],
        "location": row[2],
        "job_url": row[3],
        "date_scraped": str(row[4])
    } for row in rows]
