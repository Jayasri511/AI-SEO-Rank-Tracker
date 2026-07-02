import streamlit as st
import requests
import pandas as pd
from datetime import datetime

st.set_page_config(
    page_title="AI SEO Rank Tracker",
    page_icon="🚀",
    layout="wide"
)

API_REGISTER = "https://ai-seo-rank-tracker.onrender.com/register"
API_LOGIN = "https://ai-seo-rank-tracker.onrender.com/login"
API_ANALYSIS = "https://ai-seo-rank-tracker.onrender.com/seo-analysis"
API_HISTORY = "https://ai-seo-rank-tracker.onrender.com/seo-history"

st.title("🚀 AI SEO Rank Tracker")
st.write("Professional SEO Rank Tracking and Competitive Intelligence Platform")

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "user" not in st.session_state:
    st.session_state.user = None

if "result" not in st.session_state:
    st.session_state.result = None


def post_api(url, payload):
    try:
        response = requests.post(url, json=payload, timeout=90)

        if response.status_code != 200:
            return None, f"Backend error: {response.status_code}"

        if response.text.strip() == "":
            return None, "Backend returned empty response."

        return response.json(), None

    except requests.exceptions.ConnectionError:
        return None, "FastAPI backend is not running. Start backend first."

    except Exception as e:
        return None, str(e)



def get_api(url, params=None):
    try:
        response = requests.get(url, params=params, timeout=30)

        if response.status_code != 200:
            return None, f"Backend error: {response.status_code}"

        if response.text.strip() == "":
            return None, "Backend returned empty response."

        return response.json(), None

    except requests.exceptions.ConnectionError:
        return None, "FastAPI backend is not running. Start backend first."

    except Exception as e:
        return None, str(e)


def logout():
    st.session_state.logged_in = False
    st.session_state.user = None
    st.session_state.result = None
    st.rerun()


if not st.session_state.logged_in:
    st.subheader("🔐 Login / Register")

    auth_tab1, auth_tab2 = st.tabs(["Login", "Register"])

    with auth_tab1:
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")

        if st.button("Login"):
            if not email or not password:
                st.warning("Please enter email and password.")
            else:
                data, error = post_api(API_LOGIN, {
                    "email": email,
                    "password": password
                })

                if error:
                    st.error("Backend not running.")
                    st.code(error)
                elif data["success"]:
                    st.session_state.logged_in = True
                    st.session_state.user = data["user"]
                    st.success("Login successful ✅")
                    st.rerun()
                else:
                    st.error(data["message"])

    with auth_tab2:
        username = st.text_input("Username", key="register_username")
        reg_email = st.text_input("Email", key="register_email")
        reg_password = st.text_input("Password", type="password", key="register_password")

        if st.button("Register"):
            if not username or not reg_email or not reg_password:
                st.warning("Please fill all fields.")
            else:
                data, error = post_api(API_REGISTER, {
                    "username": username,
                    "email": reg_email,
                    "password": reg_password
                })

                if error:
                    st.error("Backend not running.")
                    st.code(error)
                elif data["success"]:
                    st.success("Registration successful. Please login.")
                else:
                    st.error(data["message"])

    st.stop()


with st.sidebar:
    st.success(f"Logged in as: {st.session_state.user['username']}")

    page = st.radio(
        "Navigation",
        [
            "Dashboard",
            "Analyze SEO",
            "Winner Analysis",
            "AI Recommendations",
            "History",
            "Download Report",
            "AI Project Mentor",
            "Logout"
        ]
    )


if page == "Logout":
    logout()


elif page == "Dashboard":
    st.subheader("📊 SEO Dashboard")

    history, error = get_api(API_HISTORY, {"user_email": st.session_state.user["email"]})

    if error:
        st.warning("Start FastAPI backend first.")
        st.code(error)

    elif history:
        df = pd.DataFrame(history)

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Scans", len(df))
        col2.metric("Avg SEO Score", f"{round(df['seo_score'].mean(), 2)}/100")
        col3.metric("Avg Competitor Score", f"{round(df['competitor_score'].mean(), 2)}/100")
        col4.metric("Best Score", f"{df['seo_score'].max()}/100")

        st.subheader("Recent Analyses")
        st.dataframe(df.head(10), use_container_width=True)

    else:
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Scans", "0")
        col2.metric("Avg SEO Score", "0/100")
        col3.metric("Avg Competitor Score", "0/100")
        col4.metric("Best Score", "0/100")
        st.info("No SEO scans yet. Go to Analyze SEO.")


elif page == "Analyze SEO":
    st.subheader("🔍 Analyze SEO")

    with st.form("seo_form"):
        col1, col2 = st.columns(2)

        with col1:
            website_url = st.text_input("Website URL", placeholder="https://www.nike.com")
            keyword = st.text_input("Target Keyword", placeholder="running shoes")

        with col2:
            competitor_url = st.text_input("Competitor URL", placeholder="https://www.adidas.com")
            location = st.selectbox("Target Location", ["India", "USA", "UK", "Global"])

        submit = st.form_submit_button("Generate SEO Report")

    if submit:
        if not website_url or not competitor_url or not keyword:
            st.warning("Please fill all fields.")
        else:
            payload = {
                "website_url": website_url,
                "competitor_url": competitor_url,
                "keyword": keyword,
                "location": location,
                "user_email": st.session_state.user["email"]
            }

            with st.spinner("Analyzing SEO ranking signals..."):
                result, error = post_api(API_ANALYSIS, payload)

            if error:
                st.error("FastAPI backend is not running.")
                st.code(error)
            else:
                st.session_state.result = result
                metrics = result["metrics"]

                st.success("SEO Analysis Completed ✅")

                col1, col2, col3, col4 = st.columns(4)

                col1.metric("SEO Score", f"{metrics['seo_score']}/100")
                col2.metric("Competitor Score", f"{metrics['competitor_score']}/100")
                col3.metric("Ranking Potential", metrics["ranking_potential"])
                col4.metric("Keyword Difficulty", metrics["keyword_difficulty"])

                st.divider()

                st.subheader("Winner Analysis")

                col1, col2 = st.columns(2)

                with col1:
                    st.write("**Competitive Position:**")
                    st.success(metrics["competitive_position"])

                    st.write("**Business Opportunity:**")
                    st.info(metrics["business_opportunity"])

                with col2:
                    st.write("**Growth Potential:**")
                    st.success(metrics["growth_potential"])

                    st.write("**Risk Level:**")
                    if metrics["risk_level"] == "High":
                        st.error(metrics["risk_level"])
                    elif metrics["risk_level"] == "Medium":
                        st.warning(metrics["risk_level"])
                    else:
                        st.success(metrics["risk_level"])

                st.divider()

                st.subheader("AI Recommendations")
                for rec in metrics["recommendations"]:
                    st.write(f"✓ {rec}")


elif page == "Winner Analysis":
    st.subheader("🏆 Winner Analysis")

    if not st.session_state.result:
        st.warning("Please run SEO analysis first.")
    else:
        result = st.session_state.result
        metrics = result["metrics"]

        col1, col2 = st.columns(2)

        with col1:
            st.metric("Your SEO Score", f"{metrics['seo_score']}/100")
            st.write(result["input"]["website_url"])

        with col2:
            st.metric("Competitor Score", f"{metrics['competitor_score']}/100")
            st.write(result["input"]["competitor_url"])

        if metrics["seo_score"] > metrics["competitor_score"]:
            st.success("Your website is currently stronger than the competitor for this keyword.")
        elif metrics["seo_score"] < metrics["competitor_score"]:
            st.error("Competitor is stronger. Optimization is required.")
        else:
            st.info("Both websites are almost equal.")


elif page == "AI Recommendations":
    st.subheader("🤖 AI Recommendations")

    if not st.session_state.result:
        st.warning("Please run SEO analysis first.")
    else:
        metrics = st.session_state.result["metrics"]

        for rec in metrics["recommendations"]:
            st.write(f"✅ {rec}")

        st.subheader("AI Generated Report")
        st.info(metrics["ai_report"])


elif page == "History":
    st.subheader("📚 SEO History")

    history, error = get_api(API_HISTORY, {"user_email": st.session_state.user["email"]})

    if error:
        st.error("Backend not running.")
        st.code(error)
    elif history:
        st.dataframe(pd.DataFrame(history), use_container_width=True)
    else:
        st.info("No history available yet.")


elif page == "Download Report":
    st.subheader("📄 Download SEO Report")

    if not st.session_state.result:
        st.warning("Please run SEO analysis first.")
    else:
        result = st.session_state.result
        metrics = result["metrics"]

        report = f"""
AI SEO RANK TRACKER REPORT

Date: {datetime.now().strftime('%d-%m-%Y')}

User:
{st.session_state.user['username']} ({st.session_state.user['email']})

Website URL:
{result['input']['website_url']}

Competitor URL:
{result['input']['competitor_url']}

Target Keyword:
{result['input']['keyword']}

Location:
{result['input']['location']}

------------------------------------------------

SEO Score             {metrics['seo_score']}
Competitor Score      {metrics['competitor_score']}
Ranking Potential     {metrics['ranking_potential']}
Keyword Difficulty    {metrics['keyword_difficulty']}

------------------------------------------------

Winner Analysis

Competitive Position:
{metrics['competitive_position']}

Business Opportunity:
{metrics['business_opportunity']}

Growth Potential:
{metrics['growth_potential']}

Risk Level:
{metrics['risk_level']}

------------------------------------------------

AI Recommendations

{chr(10).join(["✓ " + rec for rec in metrics["recommendations"]])}

------------------------------------------------

AI Report

{metrics['ai_report']}
"""

        st.text_area("Report Preview", report, height=500)

        st.download_button(
            "📥 Download SEO Report",
            data=report,
            file_name="ai_seo_rank_tracker_report.txt",
            mime="text/plain"
        )


elif page == "AI Project Mentor":
    st.subheader("🎓 AI Project Mentor")
    st.write("Select category and viva question to get a professional answer.")

    viva_categories = {
        "Project Overview": {
            "What is this project?": "This project is an AI-Powered SEO Rank Tracker and Competitive Intelligence Platform. It analyzes a website, competitor website, and target keyword to calculate SEO score, competitor score, ranking potential, keyword difficulty, winner analysis, and AI-based SEO recommendations.",
            "What problem does this project solve?": "This project solves the problem of manually checking website SEO performance and competitor strength. It helps users understand how well their website is optimized for a keyword and what improvements are needed to compete better.",
            "Who can use this project?": "Website owners, bloggers, digital marketers, small businesses, students, and SEO beginners can use this project to understand SEO performance and competitor position.",
            "What is the final output?": "The final output includes SEO score, competitor score, ranking potential, keyword difficulty, competitive position, business opportunity, growth potential, risk level, recommendations, history, and downloadable SEO report.",
            "How will you explain this project in one minute?": "This project is an AI-Powered SEO Rank Tracker built using Streamlit, FastAPI, SQLite, and Gemini. It takes a website URL, competitor URL, and keyword as input. The backend analyzes SEO signals such as title, meta description, keyword usage, content length, and links. It calculates SEO score, competitor score, keyword difficulty, ranking potential, and gives AI-based recommendations. The system also stores history and generates downloadable reports."
        },

        "Agents": {
            "What are the agents used in this project?": "This project uses five agents: SEO Audit Agent, Competitor Intelligence Agent, Ranking Prediction Agent, Recommendation Agent, and AI Project Mentor Agent. Together, these agents form a Multi-Agent SEO Intelligence System.",
            "What is the SEO Audit Agent?": "The SEO Audit Agent analyzes the target website. It checks website accessibility, title, meta description, keyword presence, content length, and link count. Based on these signals, it calculates the SEO score.",
            "What is the Competitor Intelligence Agent?": "The Competitor Intelligence Agent analyzes the competitor website using the same SEO scoring method. It compares competitor score with the user's website score and identifies which website is stronger.",
            "What is the Ranking Prediction Agent?": "The Ranking Prediction Agent estimates keyword difficulty, ranking potential, growth potential, and risk level. It helps determine whether the website has a good chance to compete for the selected keyword.",
            "What is the Recommendation Agent?": "The Recommendation Agent generates actionable SEO suggestions such as improving page title, meta description, keyword usage, content depth, internal links, and long-tail keyword strategy.",
            "What is the AI Project Mentor Agent?": "The AI Project Mentor Agent helps explain the project during viva or demonstration. It answers questions about architecture, modules, technologies, AI usage, limitations, and future scope.",
            "Why is this called a multi-agent system?": "It is called a multi-agent system because the project is divided into specialized agents. Each agent performs a specific task and together they provide complete SEO intelligence."
        },

        "Architecture": {
            "What is the architecture of this project?": "The architecture is: User Input → Streamlit Frontend → FastAPI Backend → SEO Analysis Engine → Competitor Analysis → Recommendation Engine → SQLite Storage → Dashboard and Report Output.",
            "What is the frontend?": "The frontend is built using Streamlit. It provides login, dashboard, SEO analysis, winner analysis, recommendations, history, downloadable reports, and viva mentor pages.",
            "What is the backend?": "The backend is built using FastAPI. It receives input from Streamlit, performs SEO analysis, compares competitor data, calculates scores, stores history, and returns results to the frontend.",
            "What is the database?": "SQLite is used as the database. It stores user login details and SEO analysis history.",
            "How does frontend communicate with backend?": "Streamlit sends HTTP requests to FastAPI endpoints such as /register, /login, /seo-analysis, and /seo-history. FastAPI processes the request and sends JSON responses back.",
            "What are the APIs used?": "The APIs include /register for user registration, /login for authentication, /seo-analysis for SEO analysis, and /seo-history for retrieving user-specific history."
        },

        "Technology": {
            "Why did you use Streamlit?": "Streamlit is used because it allows quick development of interactive AI dashboards. It is simple, professional, and suitable for AI/data projects.",
            "Why did you use FastAPI?": "FastAPI is used because it is fast, lightweight, supports REST APIs, validates inputs using Pydantic, and integrates easily with Python-based AI and analysis logic.",
            "Why did you use SQLite?": "SQLite is used because it is lightweight, serverless, easy to configure, and suitable for academic prototypes without needing complex database setup.",
            "Why did you use Gemini AI?": "Gemini AI is used to generate professional SEO reports and recommendations. It improves explanation quality and makes the system more intelligent.",
            "What is BeautifulSoup used for?": "BeautifulSoup is used to parse webpage HTML content. It helps extract title, meta description, visible text, and links from the website.",
            "What is Requests used for?": "Requests is used to send HTTP requests to websites and fetch their HTML content for SEO analysis.",
            "What is Pandas used for?": "Pandas is used to display history and tabular data in the Streamlit dashboard.",
            "What is Pydantic used for?": "Pydantic validates incoming request data in FastAPI, such as email, password, website URL, competitor URL, keyword, and location."
        },

        "SEO Concepts": {
            "How is SEO score calculated?": "SEO score is calculated using URL validity, website accessibility, title availability, meta description availability, keyword presence in title, keyword presence in description, keyword presence in content, content length, and link count.",
            "How is competitor score calculated?": "Competitor score is calculated using the same method as the target website. Both websites are analyzed under equal conditions and compared.",
            "What is keyword difficulty?": "Keyword difficulty indicates how hard it is to rank for a keyword. Single-word keywords are high difficulty, two-word keywords are medium difficulty, and long-tail keywords are low difficulty.",
            "What is ranking potential?": "Ranking potential estimates how likely a website can improve its search visibility for the selected keyword. It is calculated using SEO score, competitor score, and keyword difficulty.",
            "What is winner analysis?": "Winner analysis compares the user's SEO score with the competitor score. It determines whether the user's website is stronger, weaker, or close to the competitor.",
            "What is risk level?": "Risk level represents how difficult it may be to compete for the selected keyword. It depends on keyword difficulty and competitor strength.",
            "What is business opportunity?": "Business opportunity indicates whether the selected keyword and website condition provide a good chance for SEO growth and improved visibility.",
            "What is growth potential?": "Growth potential shows how much improvement opportunity the website has compared to the competitor."
        },

        "Login and Security": {
            "Why did you add login/register?": "Login/register makes the project more professional by allowing individual users to access their own SEO history and reports.",
            "What user details are stored?": "The system stores username, email, hashed password, and registration timestamp.",
            "Is the password stored directly?": "No. The password is hashed using SHA-256 before storing in SQLite. This is better than storing plain text passwords.",
            "How is user-specific history maintained?": "Each SEO report is stored with the user's email. When the user logs in, only reports related to that email are shown.",
            "Can multiple users use this project?": "Yes. Multiple users can register and login. Each user has separate analysis history."
        },

        "AI Usage": {
            "Where is AI used?": "AI is used in SEO recommendation generation, executive report generation, winner analysis explanation, and project mentor support.",
            "Is this project fully AI-based?": "The project uses a hybrid approach. Rule-based logic calculates SEO scores, while Gemini AI generates professional recommendations and reports.",
            "What happens if Gemini fails?": "If Gemini fails due to quota or API issues, the system still works using rule-based recommendations and prepared viva mentor answers.",
            "Why not depend only on Gemini?": "The core analysis is rule-based to ensure reliability. Gemini improves explanation and report quality but the system does not fail if Gemini is unavailable."
        },

        "Limitations and Future Scope": {
            "What are the limitations?": "The system does not fetch live Google SERP rankings, backlink data, or Google Search Console data. Some websites may block scraping. Gemini quota may also affect AI reports.",
            "What is the future scope?": "Future scope includes SERP API integration, Google Search Console integration, backlink analysis, page speed scoring, scheduled keyword tracking, cloud database, and deployment.",
            "Can this project be deployed?": "Yes. The frontend can be deployed on Streamlit Cloud and the backend can be deployed on Render or Railway. SQLite can be replaced with PostgreSQL for production.",
            "Can it support real-time rank tracking?": "Yes. It can be extended using SERP APIs to fetch actual Google ranking positions and track keyword rank changes over time.",
            "Can it support multiple users in production?": "Yes. The current login system supports multiple users locally. For production, a cloud database and secure authentication can be added."
        },

        "Conclusion": {
            "What is the novelty of this project?": "The novelty is combining SEO audit, competitor intelligence, ranking prediction, AI recommendations, history tracking, reports, login system, and project mentor support in one platform.",
            "What is the final conclusion?": "The project successfully demonstrates an AI-powered SEO analysis platform that calculates SEO performance, compares competitors, predicts ranking potential, gives recommendations, stores user-specific history, and generates reports.",
            "How does this help digital marketing?": "It helps digital marketing by identifying SEO weaknesses, comparing competitors, estimating keyword difficulty, and giving improvement suggestions for better search visibility.",
            "Difference from normal SEO tools?": "Normal SEO tools often provide complex technical data. This project focuses on simplified SEO scoring, competitor comparison, AI recommendations, user history, and student-friendly explanation."
        }
    }

    category = st.selectbox("Select Category", list(viva_categories.keys()))
    question = st.selectbox("Select HOD/Viva Question", list(viva_categories[category].keys()))

    if st.button("Show Perfect Answer"):
        st.success("Answer")
        st.write(viva_categories[category][question])