import { useState, useEffect } from "react";
import axios from "axios";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, PieChart, Pie, Cell
} from "recharts";

const API = "http://127.0.0.1:8000";

const COLORS = ["#6366f1", "#8b5cf6", "#a78bfa", "#c4b5fd", "#ddd6fe", "#e0e7ff"];

function StatCard({ label, value, sub }) {
  return (
    <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-100 flex flex-col gap-1">
      <p className="text-xs font-semibold uppercase tracking-widest text-slate-400">{label}</p>
      <p className="text-4xl font-bold text-slate-800">{value ?? "—"}</p>
      {sub && <p className="text-xs text-slate-400 mt-1">{sub}</p>}
    </div>
  );
}

function InsightCard({ text }) {
  const lines = text?.split("\n").filter(Boolean) || [];
  return (
    <div className="bg-gradient-to-br from-indigo-50 to-purple-50 rounded-2xl p-6 border border-indigo-100">
      <p className="text-xs font-semibold uppercase tracking-widest text-indigo-400 mb-4">AI Insights</p>
      <div className="flex flex-col gap-3">
        {lines.map((line, i) => (
          <p key={i} className="text-sm text-slate-700 leading-relaxed">{line}</p>
        ))}
      </div>
    </div>
  );
}

function JobCard({ job }) {
  return (
    <a
      href={job.job_url}
      target="_blank"
      rel="noreferrer"
      className="block bg-white rounded-xl p-4 border border-slate-100 shadow-sm hover:shadow-md hover:border-indigo-200 transition-all"
    >
      <div className="flex justify-between items-start gap-2">
        <div>
          <p className="font-semibold text-slate-800 text-sm">{job.title}</p>
          <p className="text-xs text-slate-500 mt-0.5">{job.company}</p>
        </div>
        <span className="text-xs bg-indigo-50 text-indigo-600 px-2 py-1 rounded-full whitespace-nowrap">
          {job.location?.split("\n")[0] || "Remote"}
        </span>
      </div>
      {job.skills?.length > 0 && (
        <div className="flex flex-wrap gap-1 mt-3">
          {job.skills.slice(0, 4).map((s, i) => (
            <span key={i} className="text-xs bg-slate-100 text-slate-600 px-2 py-0.5 rounded-full">
              {s}
            </span>
          ))}
        </div>
      )}
    </a>
  );
}

export default function App() {
  const [stats, setStats] = useState(null);
  const [skills, setSkills] = useState([]);
  const [companies, setCompanies] = useState([]);
  const [jobs, setJobs] = useState([]);
  const [insights, setInsights] = useState(null);
  const [search, setSearch] = useState("");
  const [searchResults, setSearchResults] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAll = async () => {
      try {
        const [s, sk, co, j, ins] = await Promise.all([
          axios.get(`${API}/stats`),
          axios.get(`${API}/skills/trending?limit=10`),
          axios.get(`${API}/companies/hiring?limit=8`),
          axios.get(`${API}/jobs/latest?limit=9`),
          axios.get(`${API}/insights`),
        ]);
        setStats(s.data);
        setSkills(sk.data);
        setCompanies(co.data);
        setJobs(j.data);
        setInsights(ins.data);
      } catch (e) {
        console.error("API error:", e);
      } finally {
        setLoading(false);
      }
    };
    fetchAll();
  }, []);

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!search.trim()) return;
    try {
      const res = await axios.get(`${API}/jobs/search?q=${search}`);
      setSearchResults(res.data);
    } catch (e) {
      console.error(e);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-10 h-10 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-slate-500 text-sm">Loading job market data...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 font-sans">

      {/* Header */}
      <div className="bg-white border-b border-slate-100 px-8 py-5 flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-slate-800 tracking-tight">
            Job Market Intelligence
          </h1>
          <p className="text-xs text-slate-400 mt-0.5">
            Real-time ML & Data Science job trends
          </p>
        </div>
        <span className="text-xs bg-green-50 text-green-600 border border-green-100 px-3 py-1 rounded-full font-medium">
          ● Live
        </span>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-8 space-y-8">

        {/* KPI Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <StatCard label="Total Jobs" value={stats?.total_jobs} sub="scraped from the web" />
          <StatCard label="Companies" value={stats?.total_companies} sub="unique hiring companies" />
          <StatCard label="Skill Mentions" value={stats?.total_skill_mentions} sub="across all job posts" />
          <StatCard label="Unique Skills" value={stats?.unique_skills} sub="distinct skills tracked" />
        </div>

        {/* Insights */}
        {insights && <InsightCard text={insights.insights} />}

        {/* Charts row */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">

          {/* Skills bar chart */}
          <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-100">
            <p className="text-xs font-semibold uppercase tracking-widest text-slate-400 mb-6">
              Trending Skills
            </p>
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={skills} layout="vertical" margin={{ left: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis type="number" tick={{ fontSize: 11, fill: "#94a3b8" }} />
                <YAxis type="category" dataKey="skill" tick={{ fontSize: 11, fill: "#64748b" }} width={90} />
                <Tooltip
                  contentStyle={{ borderRadius: 8, border: "1px solid #e2e8f0", fontSize: 12 }}
                  formatter={(v) => [v, "jobs"]}
                />
                <Bar dataKey="count" radius={[0, 4, 4, 0]}>
                  {skills.map((_, i) => (
                    <Cell key={i} fill={COLORS[i % COLORS.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Companies pie chart */}
          <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-100">
            <p className="text-xs font-semibold uppercase tracking-widest text-slate-400 mb-6">
              Top Hiring Companies
            </p>
            <ResponsiveContainer width="100%" height={280}>
              <PieChart>
                <Pie
                  data={companies}
                  dataKey="job_count"
                  nameKey="company"
                  cx="50%"
                  cy="50%"
                  outerRadius={100}
                  innerRadius={50}
                  label={({ company, percent }) =>
                    `${company.split(" ")[0]} ${(percent * 100).toFixed(0)}%`
                  }
                  labelLine={false}
                >
                  {companies.map((_, i) => (
                    <Cell key={i} fill={COLORS[i % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{ borderRadius: 8, border: "1px solid #e2e8f0", fontSize: 12 }}
                  formatter={(v, n) => [v + " jobs", n]}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Search */}
        <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-100">
          <p className="text-xs font-semibold uppercase tracking-widest text-slate-400 mb-4">
            Search Jobs
          </p>
          <form onSubmit={handleSearch} className="flex gap-3">
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search by title or company..."
              className="flex-1 px-4 py-2.5 rounded-xl border border-slate-200 text-sm text-slate-700 focus:outline-none focus:ring-2 focus:ring-indigo-300"
            />
            <button
              type="submit"
              className="bg-indigo-600 text-white px-5 py-2.5 rounded-xl text-sm font-medium hover:bg-indigo-700 transition-colors"
            >
              Search
            </button>
          </form>
          {searchResults.length > 0 && (
            <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-3">
              {searchResults.map((job, i) => (
                <JobCard key={i} job={job} />
              ))}
            </div>
          )}
        </div>

        {/* Latest jobs */}
        <div>
          <p className="text-xs font-semibold uppercase tracking-widest text-slate-400 mb-4">
            Latest Jobs
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {jobs.map((job, i) => (
              <JobCard key={i} job={job} />
            ))}
          </div>
        </div>

        {/* Footer */}
        <div className="text-center text-xs text-slate-300 pb-4">
          Built by Shreya V · Data updates daily · Powered by FastAPI + React
        </div>

      </div>
    </div>
  );
}
