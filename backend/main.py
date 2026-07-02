from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from google import genai
from bs4 import BeautifulSoup
import requests
import sqlite3
import os
import hashlib
from datetime import datetime
from urllib.parse import urlparse

load_dotenv()

app = FastAPI(title="AI SEO Rank Tracker Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key) if api_key else None

DB_NAME = "seo_rank_tracker.db"


class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class SEORequest(BaseModel):
    website_url: str
    competitor_url: str
    keyword: str
    location: str = "India"
    user_email: str = "guest"


class MentorRequest(BaseModel):
    question: str


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            email TEXT UNIQUE,
            password TEXT,
            created_at TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS seo_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT,
            website_url TEXT,
            competitor_url TEXT,
            keyword TEXT,
            location TEXT,
            seo_score INTEGER,
            competitor_score INTEGER,
            winner TEXT,
            competitive_position TEXT,
            current_rank INTEGER,
            competitor_rank INTEGER,
            rank_difference INTEGER,
            ranking_potential TEXT,
            keyword_difficulty TEXT,
            business_opportunity TEXT,
            growth_potential TEXT,
            risk_level TEXT,
            expected_improvement TEXT,
            priority TEXT,
            ai_recommendations TEXT,
            ai_report TEXT,
            created_at TEXT
        )
    """)

    conn.commit()
    conn.close()


init_db()


def fetch_page_data(url, keyword):
    result = {
        "url": url,
        "reachable": False,
        "title": "",
        "meta_description": "",
        "content_length": 0,
        "word_count": 0,
        "link_count": 0,
        "keyword_in_title": False,
        "keyword_in_description": False,
        "keyword_in_content": False,
        "score": 0,
    }

    try:
        if not url.startswith("http"):
            url = "https://" + url

        result["url"] = url
        parsed = urlparse(url)

        if parsed.scheme and parsed.netloc:
            result["score"] += 10

        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=12)

        if response.status_code == 200:
            result["reachable"] = True
            result["score"] += 20

        soup = BeautifulSoup(response.text, "html.parser")

        title = soup.title.string.strip() if soup.title and soup.title.string else ""
        meta = soup.find("meta", attrs={"name": "description"})
        meta_desc = meta.get("content", "").strip() if meta else ""

        text = soup.get_text(separator=" ", strip=True)
        links = soup.find_all("a")

        keyword_lower = keyword.lower()

        result["title"] = title
        result["meta_description"] = meta_desc
        result["content_length"] = len(text)
        result["word_count"] = len(text.split())
        result["link_count"] = len(links)

        if title:
            result["score"] += 15

        if meta_desc:
            result["score"] += 15

        if keyword_lower in title.lower():
            result["keyword_in_title"] = True
            result["score"] += 15

        if keyword_lower in meta_desc.lower():
            result["keyword_in_description"] = True
            result["score"] += 10

        if keyword_lower in text.lower():
            result["keyword_in_content"] = True
            result["score"] += 15

        if len(text) > 1500:
            result["score"] += 10

        if len(links) >= 20:
            result["score"] += 10

        result["score"] = min(result["score"], 100)

    except Exception as e:
        result["error"] = str(e)

    return result


def get_competitive_position(seo_score, competitor_score):
    if seo_score > competitor_score:
        return "Strong"
    elif seo_score == competitor_score:
        return "Equal"
    elif competitor_score - seo_score <= 10:
        return "Moderate"
    return "Needs Improvement"


class SEOAuditAgent:
    def run(self, website_url, keyword):
        site_data = fetch_page_data(website_url, keyword)

        return {
            "agent_name": "SEO Audit Agent",
            "website_data": site_data,
            "seo_score": site_data["score"],
        }


class CompetitorIntelligenceAgent:
    def run(self, competitor_url, keyword, website_score):
        competitor_data = fetch_page_data(competitor_url, keyword)
        competitor_score = competitor_data["score"]

        if website_score > competitor_score:
            winner = "Your Website"
        elif competitor_score > website_score:
            winner = "Competitor Website"
        else:
            winner = "Tie"

        return {
            "agent_name": "Competitor Intelligence Agent",
            "competitor_data": competitor_data,
            "competitor_score": competitor_score,
            "winner": winner,
            "score_difference": abs(website_score - competitor_score),
        }


class RankTrackingAgent:
    def run(self, seo_score, competitor_score, keyword):
        if seo_score >= 90:
            current_rank = 1
        elif seo_score >= 80:
            current_rank = 3
        elif seo_score >= 70:
            current_rank = 7
        elif seo_score >= 60:
            current_rank = 15
        elif seo_score >= 50:
            current_rank = 25
        else:
            current_rank = 40

        if competitor_score >= 90:
            competitor_rank = 1
        elif competitor_score >= 80:
            competitor_rank = 3
        elif competitor_score >= 70:
            competitor_rank = 7
        elif competitor_score >= 60:
            competitor_rank = 15
        elif competitor_score >= 50:
            competitor_rank = 25
        else:
            competitor_rank = 40

        if current_rank < competitor_rank:
            rank_status = "Your website ranks better"
        elif competitor_rank < current_rank:
            rank_status = "Competitor ranks better"
        else:
            rank_status = "Both websites have similar rank position"

        return {
            "agent_name": "Rank Tracking Agent",
            "keyword": keyword,
            "current_rank": current_rank,
            "competitor_rank": competitor_rank,
            "rank_difference": abs(current_rank - competitor_rank),
            "rank_status": rank_status,
        }


class RankingPredictionAgent:
    def keyword_difficulty(self, keyword):
        words = keyword.split()

        if len(words) <= 1:
            return "Hard"
        elif len(words) == 2:
            return "Medium"
        return "Easy"

    def ranking_potential(self, seo_score, competitor_score, difficulty):
        if seo_score >= competitor_score and difficulty != "Hard":
            return "High"
        elif seo_score >= 70 or abs(seo_score - competitor_score) <= 10:
            return "Medium"
        return "Low"

    def run(self, seo_score, competitor_score, keyword):
        difficulty = self.keyword_difficulty(keyword)
        potential = self.ranking_potential(seo_score, competitor_score, difficulty)

        business = "High" if potential == "High" else "Medium" if potential == "Medium" else "Low"

        gap = competitor_score - seo_score

        if gap <= 0:
            growth = "High"
            expected_improvement = "+5% to +10%"
            priority = "Medium"
        elif gap <= 10:
            growth = "Good"
            expected_improvement = "+10% to +20%"
            priority = "High"
        elif gap <= 25:
            growth = "Medium"
            expected_improvement = "+20% to +35%"
            priority = "High"
        else:
            growth = "Needs Improvement"
            expected_improvement = "+35% to +50%"
            priority = "Critical"

        if difficulty == "Hard" and competitor_score >= 80:
            risk = "High"
        elif difficulty == "Medium":
            risk = "Medium"
        else:
            risk = "Low"

        return {
            "agent_name": "Ranking Prediction Agent",
            "keyword_difficulty": difficulty,
            "ranking_potential": potential,
            "business_opportunity": business,
            "growth_potential": growth,
            "risk_level": risk,
            "expected_improvement": expected_improvement,
            "priority": priority,
        }


class RecommendationAgent:
    def run(self, site_data, competitor_data, keyword):
        recs = []

        if not site_data.get("keyword_in_title"):
            recs.append("Add the target keyword in the page title.")

        if not site_data.get("keyword_in_description"):
            recs.append("Improve the meta description using the target keyword.")

        if not site_data.get("keyword_in_content"):
            recs.append("Add keyword variations naturally inside the page content.")

        if site_data.get("content_length", 0) < competitor_data.get("content_length", 0):
            recs.append("Improve content depth to compete with competitor coverage.")

        if site_data.get("link_count", 0) < competitor_data.get("link_count", 0):
            recs.append("Improve internal linking and navigation structure.")

        recs.append("Track keyword ranking weekly.")
        recs.append("Create supporting blog content around long-tail keywords.")

        return {
            "agent_name": "Recommendation Agent",
            "recommendations": recs,
        }


class AIProjectMentorAgent:
    def run(self, question):
        q = question.lower()

        answers = {
            "what is this project": "This project is an AI-powered SEO Rank Tracker and Competitive Intelligence Platform using a multi-agent architecture.",
            "technologies": "The project uses Streamlit, FastAPI, SQLite, BeautifulSoup, Requests, Pandas, and Gemini AI.",
            "agents": "The agents are SEO Audit Agent, Competitor Intelligence Agent, Rank Tracking Agent, Ranking Prediction Agent, Recommendation Agent, and AI Project Mentor Agent.",
            "future scope": "Future scope includes real-time Google ranking, backlink analysis, analytics integration, PDF reports, and cloud deployment.",
            "advantages": "The main advantages are automation, competitor comparison, rank tracking, SEO scoring, AI recommendations, history tracking, and project mentoring.",
        }

        for key, value in answers.items():
            if key in q:
                return {"agent_name": "AI Project Mentor Agent", "answer": value}

        if client:
            try:
                response = client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=f"Answer this project viva question clearly: {question}",
                )
                return {"agent_name": "AI Project Mentor Agent", "answer": response.text}
            except Exception:
                pass

        return {
            "agent_name": "AI Project Mentor Agent",
            "answer": "This project analyzes website SEO performance, compares competitors, tracks estimated rank position, predicts ranking potential, and provides AI-based recommendations.",
        }


def gemini_report(data, final_metrics):
    fallback = f"""
AI SEO Recommendation Report

Website: {data.website_url}
Competitor: {data.competitor_url}
Keyword: {data.keyword}
Location: {data.location}

SEO Score: {final_metrics['seo_score']}
Competitor Score: {final_metrics['competitor_score']}
Winner: {final_metrics['winner']}
Competitive Position: {final_metrics['competitive_position']}

Current Estimated Rank: {final_metrics['current_rank']}
Competitor Estimated Rank: {final_metrics['competitor_rank']}
Rank Difference: {final_metrics['rank_difference']}
Rank Status: {final_metrics['rank_status']}

Ranking Potential: {final_metrics['ranking_potential']}
Keyword Difficulty: {final_metrics['keyword_difficulty']}
Business Opportunity: {final_metrics['business_opportunity']}
Growth Potential: {final_metrics['growth_potential']}
Risk Level: {final_metrics['risk_level']}
Expected Improvement: {final_metrics['expected_improvement']}
Priority: {final_metrics['priority']}

Recommendation:
Improve content depth, add keyword variations, strengthen internal links, and monitor keyword ranking weekly.
"""

    if not client:
        return fallback

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=f"""
You are a professional SEO consultant.

Generate a concise SEO report for:

Website: {data.website_url}
Competitor: {data.competitor_url}
Keyword: {data.keyword}
Location: {data.location}

Metrics:
{final_metrics}

Include:
1. SEO Summary
2. Winner Analysis
3. Rank Tracking Summary
4. Keyword Opportunity
5. Competitor Gap
6. AI Recommendations
7. 7-Day Action Plan
""",
        )
        return response.text
    except Exception:
        return fallback


class MultiAgentOrchestrator:
    def run(self, data):
        seo_agent = SEOAuditAgent()
        competitor_agent = CompetitorIntelligenceAgent()
        rank_agent = RankTrackingAgent()
        ranking_agent = RankingPredictionAgent()
        recommendation_agent = RecommendationAgent()

        seo_result = seo_agent.run(data.website_url, data.keyword)

        competitor_result = competitor_agent.run(
            data.competitor_url,
            data.keyword,
            seo_result["seo_score"],
        )

        rank_result = rank_agent.run(
            seo_result["seo_score"],
            competitor_result["competitor_score"],
            data.keyword,
        )

        ranking_result = ranking_agent.run(
            seo_result["seo_score"],
            competitor_result["competitor_score"],
            data.keyword,
        )

        recommendation_result = recommendation_agent.run(
            seo_result["website_data"],
            competitor_result["competitor_data"],
            data.keyword,
        )

        final_metrics = {
            "seo_score": seo_result["seo_score"],
            "competitor_score": competitor_result["competitor_score"],
            "winner": competitor_result["winner"],
            "competitive_position": get_competitive_position(
                seo_result["seo_score"],
                competitor_result["competitor_score"],
            ),
            "current_rank": rank_result["current_rank"],
            "competitor_rank": rank_result["competitor_rank"],
            "rank_difference": rank_result["rank_difference"],
            "rank_status": rank_result["rank_status"],
            "ranking_potential": ranking_result["ranking_potential"],
            "keyword_difficulty": ranking_result["keyword_difficulty"],
            "business_opportunity": ranking_result["business_opportunity"],
            "growth_potential": ranking_result["growth_potential"],
            "risk_level": ranking_result["risk_level"],
            "expected_improvement": ranking_result["expected_improvement"],
            "priority": ranking_result["priority"],
            "recommendations": recommendation_result["recommendations"],
        }

        final_metrics["ai_report"] = gemini_report(data, final_metrics)

        return {
            "input": data.dict(),
            "agents_used": [
                "SEO Audit Agent",
                "Competitor Intelligence Agent",
                "Rank Tracking Agent",
                "Ranking Prediction Agent",
                "Recommendation Agent",
                "AI Project Mentor Agent",
            ],
            "seo_audit_agent": seo_result,
            "competitor_intelligence_agent": competitor_result,
            "rank_tracking_agent": rank_result,
            "ranking_prediction_agent": ranking_result,
            "recommendation_agent": recommendation_result,
            "metrics": final_metrics,
        }


def save_report(data, final_metrics):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""
        INSERT INTO seo_reports (
            user_email, website_url, competitor_url, keyword, location,
            seo_score, competitor_score, winner, competitive_position,
            current_rank, competitor_rank, rank_difference,
            ranking_potential, keyword_difficulty, business_opportunity,
            growth_potential, risk_level, expected_improvement, priority,
            ai_recommendations, ai_report, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data.user_email,
        data.website_url,
        data.competitor_url,
        data.keyword,
        data.location,
        final_metrics["seo_score"],
        final_metrics["competitor_score"],
        final_metrics["winner"],
        final_metrics["competitive_position"],
        final_metrics["current_rank"],
        final_metrics["competitor_rank"],
        final_metrics["rank_difference"],
        final_metrics["ranking_potential"],
        final_metrics["keyword_difficulty"],
        final_metrics["business_opportunity"],
        final_metrics["growth_potential"],
        final_metrics["risk_level"],
        final_metrics["expected_improvement"],
        final_metrics["priority"],
        "\n".join(final_metrics["recommendations"]),
        final_metrics["ai_report"],
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    ))

    conn.commit()
    conn.close()


@app.get("/")
def home():
    return {"message": "AI SEO Rank Tracker Backend Running Successfully"}


@app.post("/register")
def register(data: RegisterRequest):
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()

        c.execute("""
            INSERT INTO users (username, email, password, created_at)
            VALUES (?, ?, ?, ?)
        """, (
            data.username,
            data.email,
            hash_password(data.password),
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        ))

        conn.commit()
        conn.close()

        return {"success": True, "message": "Registration successful"}

    except sqlite3.IntegrityError:
        return {"success": False, "message": "Email already registered"}


@app.post("/login")
def login(data: LoginRequest):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute(
        "SELECT username, email FROM users WHERE email=? AND password=?",
        (data.email, hash_password(data.password)),
    )

    user = c.fetchone()
    conn.close()

    if user:
        return {
            "success": True,
            "message": "Login successful",
            "user": {
                "username": user[0],
                "email": user[1],
            },
        }

    return {"success": False, "message": "Invalid email or password"}


@app.post("/seo-analysis")
def seo_analysis(data: SEORequest):
    orchestrator = MultiAgentOrchestrator()
    result = orchestrator.run(data)
    save_report(data, result["metrics"])
    return result


@app.post("/project-mentor")
def project_mentor(data: MentorRequest):
    mentor = AIProjectMentorAgent()
    return mentor.run(data.question)


@app.get("/seo-history")
def seo_history(user_email: str = "guest"):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute(
        "SELECT * FROM seo_reports WHERE user_email=? ORDER BY id DESC",
        (user_email,),
    )

    rows = c.fetchall()
    conn.close()

    return [
        {
            "id": row[0],
            "user_email": row[1],
            "website_url": row[2],
            "competitor_url": row[3],
            "keyword": row[4],
            "location": row[5],
            "seo_score": row[6],
            "competitor_score": row[7],
            "winner": row[8],
            "competitive_position": row[9],
            "current_rank": row[10],
            "competitor_rank": row[11],
            "rank_difference": row[12],
            "ranking_potential": row[13],
            "keyword_difficulty": row[14],
            "business_opportunity": row[15],
            "growth_potential": row[16],
            "risk_level": row[17],
            "expected_improvement": row[18],
            "priority": row[19],
            "ai_recommendations": row[20],
            "ai_report": row[21],
            "created_at": row[22],
        }
        for row in rows
    ]