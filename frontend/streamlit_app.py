
import sys
import json
import html
import threading
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st

from frontend.api_client import APIClient
from frontend.config import APP_TITLE, APP_SUBTITLE
from frontend.careers_portal import render_careers_portal

# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title=APP_TITLE,
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)


# --------------------------------------------------
# SESSION STATE
# --------------------------------------------------

DEFAULTS = {
    "api_client": APIClient(),
    "access_token": None,
    "user_profile": None,
    "evaluation_thread_id": None,
    "uploaded_resume": None,
    "last_evaluation": None,
    "interview_result": None,
    "memories": []
}

for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value

api = st.session_state.api_client


# --------------------------------------------------
# PROFESSIONAL UI - ANIMATED RAINBOW GRADIENT
# --------------------------------------------------

def apply_custom_css():
    st.markdown("""
    <style>

    /* Main application */
    .stApp {
        background:
            radial-gradient(
                circle at 10% 10%,
                rgba(104, 55, 180, 0.13),
                transparent 35%
            ),
            radial-gradient(
                circle at 90% 20%,
                rgba(0, 180, 200, 0.10),
                transparent 35%
            ),
            #080b14;
        color: #e8edf8;
    }

    /* Hide Streamlit branding */
    #MainMenu {
        visibility: hidden;
    }

    footer {
        visibility: hidden;
    }

    header[data-testid="stHeader"] {
        background: transparent;
    }

    /* Animated rainbow gradient */
    @keyframes rainbowFlow {
        0% {
            background-position: 0% 50%;
        }
        50% {
            background-position: 100% 50%;
        }
        100% {
            background-position: 0% 50%;
        }
    }

    .rainbow-title {
        background: linear-gradient(
            90deg,
            #ff4ecd,
            #9b6bff,
            #36cfff,
            #42e8a5,
            #ffe66d,
            #ff8a5b,
            #ff4ecd
        );
        background-size: 400% 400%;
        animation: rainbowFlow 9s ease infinite;
        -webkit-background-clip: text;
        background-clip: text;
        color: transparent;
        font-weight: 850;
        letter-spacing: -1.5px;
    }

    .rainbow-line {
        height: 3px;
        width: 100%;
        border-radius: 20px;
        background: linear-gradient(
            90deg,
            #ff4ecd,
            #9b6bff,
            #36cfff,
            #42e8a5,
            #ffe66d,
            #ff8a5b
        );
        background-size: 300% 300%;
        animation: rainbowFlow 8s ease infinite;
        margin: 12px 0 24px 0;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: linear-gradient(
            180deg,
            #101626,
            #0b1020
        );
        border-right: 1px solid rgba(150, 160, 210, 0.15);
    }

    section[data-testid="stSidebar"] h1 {
        font-size: 25px;
    }

    /* Buttons */
    .stButton > button,
    .stFormSubmitButton > button {
        border: 1px solid rgba(150, 130, 255, 0.35);
        border-radius: 11px;
        background: linear-gradient(
            100deg,
            #7147dc,
            #397eea,
            #16a9b8
        );
        background-size: 200% 200%;
        color: white;
        font-weight: 650;
        transition: all 0.25s ease;
    }

    .stButton > button:hover,
    .stFormSubmitButton > button:hover {
        background-position: 100% 50%;
        border-color: #a98aff;
        transform: translateY(-2px);
        box-shadow: 0 5px 20px rgba(100, 90, 240, 0.25);
    }

    /* Input fields */
    .stTextInput input,
    .stTextArea textarea,
    .stSelectbox div[data-baseweb="select"],
    .stNumberInput input {
        background-color: #111827 !important;
        color: #f2f5ff !important;
        border-radius: 9px !important;
        border-color: #303b52 !important;
    }

    /* Cards */
    .custom-card {
        background: linear-gradient(
            145deg,
            rgba(25, 34, 55, 0.95),
            rgba(15, 22, 39, 0.95)
        );
        border: 1px solid rgba(140, 155, 205, 0.18);
        border-radius: 15px;
        padding: 20px;
        margin-bottom: 15px;
    }

    .custom-card h3 {
        color: #ffffff;
        margin-top: 0;
    }

    .muted-text {
        color: #9caac3;
        font-size: 14px;
    }

    /* Metrics */
    div[data-testid="stMetric"] {
        background: rgba(23, 32, 52, 0.85);
        border: 1px solid rgba(140, 155, 205, 0.18);
        padding: 16px;
        border-radius: 13px;
    }

    div[data-testid="stMetricLabel"] {
        color: #aab8d2;
    }

    div[data-testid="stMetricValue"] {
        color: #ffffff;
    }

    /* Expanders */
    details {
        background: rgba(20, 29, 47, 0.75);
        border: 1px solid rgba(140, 155, 205, 0.16);
        border-radius: 10px;
    }

    /* Dividers */
    hr {
        border-color: rgba(140, 155, 205, 0.17);
    }

    /* File uploader */
    [data-testid="stFileUploader"] {
        background: rgba(22, 31, 51, 0.65);
        border: 1px dashed #58658a;
        border-radius: 12px;
        padding: 10px;
    }

/* ===== PREMIUM LOGIN UI ===== */

@keyframes borderFlow {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}

@keyframes glowPulse {
    0%, 100% {
        box-shadow: 0 0 20px rgba(137, 85, 255, 0.18),
                    0 0 45px rgba(0, 190, 255, 0.08);
    }
    50% {
        box-shadow: 0 0 32px rgba(255, 65, 190, 0.25),
                    0 0 65px rgba(0, 190, 255, 0.16);
    }
}

/* Login panel */
div[data-testid="stVerticalBlockBorderWrapper"] {
    background: linear-gradient(
        145deg,
        rgba(32, 26, 60, 0.96),
        rgba(12, 24, 44, 0.97)
    ) !important;

    border: 1px solid rgba(160, 120, 255, 0.55) !important;
    border-radius: 20px !important;

    box-shadow:
        0 0 22px rgba(130, 75, 255, 0.16),
        inset 0 0 20px rgba(80, 120, 255, 0.05) !important;
}

/* Form box */
div[data-testid="stForm"] {
    background: rgba(15, 22, 43, 0.90) !important;
    border: 1px solid rgba(75, 190, 255, 0.30) !important;
    border-radius: 15px !important;
    padding: 22px !important;
    box-shadow: 0 0 24px rgba(60, 140, 255, 0.10);
}

/* Rainbow heading */
h1.rainbow-title {
    background: linear-gradient(
        90deg,
        #ff48c4,
        #a66bff,
        #35c8ff,
        #42efbd,
        #ffe66d,
        #ff8a5b,
        #ff48c4
    ) !important;

    background-size: 400% 400% !important;
    animation: rainbowFlow 7s ease infinite !important;

    -webkit-background-clip: text !important;
    background-clip: text !important;
    -webkit-text-fill-color: transparent !important;
    filter: drop-shadow(0 0 12px rgba(165, 100, 255, 0.25));
}

/* Input boxes */
div[data-testid="stTextInput"] input {
    background: #151d32 !important;
    color: #ffffff !important;
    border: 1px solid #52648c !important;
    border-radius: 10px !important;
    min-height: 46px !important;
}

div[data-testid="stTextInput"] input:focus {
    border: 1px solid #b16cff !important;
    box-shadow: 0 0 12px rgba(177, 108, 255, 0.35) !important;
}

/* Input labels */
div[data-testid="stTextInput"] label {
    color: #c6d4f5 !important;
    font-weight: 600 !important;
}

/* Login button */
.stFormSubmitButton button {
    background: linear-gradient(
        100deg,
        #9333ea,
        #536dfe,
        #06b6d4,
        #9333ea
    ) !important;

    background-size: 300% 300% !important;
    animation: borderFlow 6s ease infinite;

    border: 1px solid rgba(255,255,255,0.25) !important;
    border-radius: 11px !important;
    min-height: 48px !important;
    font-size: 16px !important;
    font-weight: 700 !important;
    color: white !important;
}

/* Login button hover */
.stFormSubmitButton button:hover {
    box-shadow: 0 0 22px rgba(135, 90, 255, 0.55) !important;
    transform: translateY(-2px);
}

/* Recruiter portal title */
div[data-testid="stForm"] h3 {
    color: #ffffff !important;
    font-size: 25px !important;
}

/* Supporting text */
div[data-testid="stForm"] p {
    color: #b9c7e5 !important;
}

/* Subtle page glow */
.stApp {
    background:
        radial-gradient(
            ellipse at 50% 15%,
            rgba(116, 65, 220, 0.22),
            transparent 42%
        ),
        radial-gradient(
            ellipse at 85% 45%,
            rgba(0, 190, 220, 0.12),
            transparent 35%
        ),
        #080b16 !important;
}

/* ===== SIDEBAR READABILITY ===== */

section[data-testid="stSidebar"] {
    background: linear-gradient(
        180deg,
        #151d35,
        #0c1326
    ) !important;
}

section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] div[data-testid="stMarkdownContainer"] {
    color: #d4def5 !important;
}

section[data-testid="stSidebar"] a {
    color: #53c9ff !important;
}

section[data-testid="stSidebar"] [data-testid="stCaptionContainer"] {
    color: #9eafd0 !important;
}

/* Navigation labels */
section[data-testid="stSidebar"] div[role="radiogroup"] label {
    color: #e1eaff !important;
    font-weight: 500;
}

/* Metric labels */
div[data-testid="stMetricLabel"] {
    color: #b9c8e8 !important;
}

/* Metric values */
div[data-testid="stMetricValue"] {
    color: #ffffff !important;
}

/* Better card hover effect */
.custom-card {
    transition: all 0.25s ease;
}

.custom-card:hover {
    border-color: #a16bff;
    transform: translateY(-3px);
    box-shadow: 0 8px 25px rgba(130, 90, 255, 0.18);
}

/* ===== DARK RESUME UPLOADER ===== */

div[data-testid="stFileUploader"] {
    background: linear-gradient(
        135deg,
        #171e36,
        #202746
    ) !important;

    border: 1px dashed #8b72e8 !important;
    border-radius: 12px !important;
    padding: 15px !important;
}

div[data-testid="stFileUploader"] section {
    background: transparent !important;
}

div[data-testid="stFileUploader"] button {
    background: linear-gradient(
        100deg,
        #8148e8,
        #397de8
    ) !important;
    color: white !important;
    border: none !important;
}

div[data-testid="stFileUploader"] small,
div[data-testid="stFileUploader"] span,
div[data-testid="stFileUploader"] label {
    color: #d4def5 !important;
}

/* ===== FORM IMPROVEMENTS ===== */

div[data-testid="stForm"] {
    background: linear-gradient(
        145deg,
        #151d34,
        #10182c
    ) !important;

    border: 1px solid #394b78 !important;
    border-radius: 16px !important;
    padding: 22px !important;
}

div[data-testid="stTextInput"] input {
    background: #0e172b !important;
    color: #ffffff !important;
    border: 1px solid #52648c !important;
    min-height: 43px !important;
}

/* ===== SECTION HEADINGS ===== */

.stApp h3 {
    color: #e5d5ff !important;
}

/* ===== EMPTY STATE ===== */

div[data-testid="stAlert"] {
    background: #172641 !important;
    border: 1px solid #397de8 !important;
    border-radius: 10px !important;
}

div[data-testid="stAlert"] p {
    color: #d9e8ff !important;
}

/* =================================
   RESUME INTELLIGENCE UI
================================= */

/* Candidate profile cards */
.resume-card {
    background: linear-gradient(
        135deg,
        #192442,
        #111a31
    );
    border: 1px solid #465a89;
    border-radius: 15px;
    padding: 19px;
    margin: 8px 0;
    box-shadow: 0 5px 20px rgba(0,0,0,0.18);
}

.resume-card-title {
    color: #aebde0;
    font-size: 12px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1px;
}

.resume-card-value {
    color: #ffffff;
    font-size: 19px;
    font-weight: 700;
    margin-top: 7px;
    overflow-wrap: anywhere;
}

.resume-section-title {
    color: #d9c5ff;
    font-size: 20px;
    font-weight: 750;
    margin: 18px 0 12px 0;
}

/* Extracted resume text */
div[data-testid="stTextArea"] textarea {
    background: #0c1529 !important;
    color: #e5edff !important;
    border: 1px solid #536a9a !important;
    border-radius: 12px !important;
    line-height: 1.65 !important;
    font-size: 14px !important;
    opacity: 1 !important;
    -webkit-text-fill-color: #e5edff !important;
}

/* Disabled text area must remain readable */
div[data-testid="stTextArea"] textarea:disabled {
    color: #e5edff !important;
    -webkit-text-fill-color: #e5edff !important;
    opacity: 1 !important;
}

/* Disabled profile inputs */
div[data-testid="stTextInput"] input:disabled {
    color: #e5edff !important;
    -webkit-text-fill-color: #e5edff !important;
    background: #111d35 !important;
    border: 1px solid #52648c !important;
    opacity: 1 !important;
}

/* Skill tags */
.skill-tag {
    display: inline-block;
    background: linear-gradient(
        110deg,
        rgba(126, 75, 225, 0.24),
        rgba(35, 155, 220, 0.20)
    );
    border: 1px solid #7860c5;
    color: #e5dcff;
    border-radius: 20px;
    padding: 6px 12px;
    margin: 4px;
    font-size: 13px;
    font-weight: 600;
}

/* Information panels */
.info-panel {
    background: #131f39;
    border: 1px solid #3d527c;
    border-radius: 12px;
    padding: 16px;
    margin: 8px 0;
    color: #dce6ff;
}

/* Section divider */
.resume-gradient-line {
    height: 2px;
    background: linear-gradient(
        90deg,
        #b44dff,
        #438dff,
        #26d9c3
    );
    margin: 22px 0;
    border-radius: 10px;
}
/* ===== DASHBOARD METRIC LABEL VISIBILITY ===== */

div[data-testid="stMetricLabel"],
div[data-testid="stMetricLabel"] p,
div[data-testid="stMetricLabel"] label,
div[data-testid="stMetricLabel"] span {
    color: #cbd5f5 !important;
    opacity: 1 !important;
    font-weight: 600 !important;
}

div[data-testid="stMetricValue"],
div[data-testid="stMetricValue"] div {
    color: #ffffff !important;
    opacity: 1 !important;
}
/* Dashboard metric label visibility fix */

[data-testid="stMetricLabel"] {
    color: #ffffff !important;
    opacity: 1 !important;
}

[data-testid="stMetricLabel"] * {
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    opacity: 1 !important;
}

[data-testid="stMetricValue"] * {
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
}

    </style>
    """, unsafe_allow_html=True)


apply_custom_css()


# --------------------------------------------------
# COMMON HELPERS
# --------------------------------------------------

def show_error(error):
    st.error(str(error))
    
def run_with_live_progress(task, title):

    result = {}
    completed = threading.Event()

    def worker():
        try:
            result["value"] = task()
        except Exception as error:
            result["error"] = error
        finally:
            completed.set()

    progress_area = st.empty()
    timer_area = st.empty()
    status_area = st.empty()

    start_time = time.perf_counter()

    progress_area.markdown(
        """
        <style>
        .hiremind-progress-track {
            width: 100%;
            height: 9px;
            background: #202b42;
            border-radius: 20px;
            overflow: hidden;
        }

        .hiremind-progress-bar {
            width: 35%;
            height: 100%;
            background: linear-gradient(
                90deg, #9333ea, #3b82f6, #22d3ee
            );
            border-radius: 20px;
            animation: hiremind-loading 1.3s ease-in-out infinite;
        }

        @keyframes hiremind-loading {
            0% { transform: translateX(-110%); }
            100% { transform: translateX(300%); }
        }
        </style>

        <div class="hiremind-progress-track">
            <div class="hiremind-progress-bar"></div>
        </div>
        """,
        unsafe_allow_html=True
    )

    status_area.info(f"⏳ {title}")

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()

    while not completed.is_set():
        elapsed = time.perf_counter() - start_time
        timer_area.caption(f"Elapsed time: {elapsed:.1f} seconds")
        time.sleep(0.2)

    thread.join()

    elapsed = time.perf_counter() - start_time

    progress_area.empty()
    timer_area.empty()
    status_area.empty()

    if "error" in result:
        raise result["error"]

    st.caption(f"✓ Completed in {elapsed:.2f} seconds")

    return result["value"]



def page_header(title, subtitle):
    st.markdown(
        f'<h1 class="rainbow-title">{title}</h1>',
        unsafe_allow_html=True
    )
    st.caption(subtitle)
    st.markdown(
        '<div class="rainbow-line"></div>',
        unsafe_allow_html=True
    )


def display_list(title, items):
    st.markdown(f"**{title}**")

    if items:
        for item in items:
            st.markdown(f"- {item}")
    else:
        st.caption("No items available.")


# --------------------------------------------------
# LOGIN PAGE
# --------------------------------------------------

def login_screen():

    st.markdown("<br><br>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.4, 1])

    with col2:
        st.markdown(
            '<h1 class="rainbow-title" '
            'style="text-align:center;font-size:42px;">'
            '🧠 AI HireMind</h1>',
            unsafe_allow_html=True
        )

        st.markdown(
            f'<p style="text-align:center;color:#aab8d2;">'
            f'{APP_SUBTITLE}</p>',
            unsafe_allow_html=True
        )

        st.markdown('<div class="rainbow-line"></div>',
                    unsafe_allow_html=True)

        with st.container(border=True):
            st.subheader("Recruiter Portal")
            st.caption("Sign in to access your recruitment workspace.")

            with st.form("login_form"):
                email = st.text_input(
                    "Email address",
                    placeholder="recruiter@example.com"
                )

                password = st.text_input(
                    "Password",
                    type="password",
                    placeholder="Enter your password"
                )

                submitted = st.form_submit_button(
                    "Sign In →",
                    use_container_width=True,
                    type="primary"
                )

            if submitted:
                if not email.strip() or not password:
                    st.warning("Enter your email and password.")
                    return

                try:
                    with st.spinner("Authenticating recruiter..."):
                        result = api.login(email.strip(), password)

                        token = result.get("access_token")

                        if not token:
                            st.error(
                                "Login response did not contain an access token."
                            )
                            return

                        api.set_token(token)
                        profile = api.get_profile()

                    if profile.get("role") not in ("recruiter", "admin"):
                        api.clear_token()
                        st.error(
                            "This dashboard is available to recruiters and admins."
                        )
                        return

                    st.session_state.access_token = token
                    st.session_state.user_profile = profile

                    st.rerun()

                except Exception as error:
                    show_error(error)


# --------------------------------------------------
# DASHBOARD
# --------------------------------------------------

def dashboard_page():

    profile = st.session_state.user_profile or {}

    page_header(
        "Recruiter Dashboard",
        "Your intelligent recruitment command center."
    )

    st.markdown("""
    <div class="custom-card">
        <h3>Welcome to AI HireMind 👋</h3>
        <p class="muted-text">
            An evidence-driven recruitment intelligence platform
            designed to support candidate evaluation, skill analysis,
            interview planning and human review.
        </p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    col1.metric("Platform", "AI HireMind")
    col2.metric("Account Role", profile.get("role", "Recruiter").title())
    col3.metric("Workspace", "Active")

    st.subheader("Recruitment Workspace")

    cards = [
        ("📄", "AI Evaluation",
         "Upload candidate resumes and analyze job fit."),
        ("💼", "Job Management",
         "View available recruitment opportunities."),
        ("🎯", "Interview Intelligence",
         "Generate structured interview questions."),
        ("🧠", "Recruiter Memory",
         "Manage saved preferences and knowledge.")
    ]

    for i in range(0, len(cards), 2):
        c1, c2 = st.columns(2)

        for column, card in zip(
            [c1, c2],
            cards[i:i + 2]
        ):
            with column:
                st.markdown(
                    f"""
                    <div class="custom-card">
                        <h3>{card[0]} {card[1]}</h3>
                        <p class="muted-text">{card[2]}</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )


# --------------------------------------------------
# AI EVALUATION PAGE
# --------------------------------------------------

def evaluation_page():

    page_header(
        "AI Candidate Evaluation",
        "Upload resumes, analyze candidate evidence and review AI-assisted results."
    )

    # --------------------------------------------------
    # 01 - RESUME UPLOAD
    # Candidate identity is extracted by the backend.
    # --------------------------------------------------

    st.markdown("### 01 · Upload Candidate Resume")

    st.caption(
        "Upload a candidate's PDF or DOCX resume. "
        "Candidate details will be extracted automatically."
    )

    with st.container(border=True):

        uploaded_file = st.file_uploader(
             "Choose candidate resume",
             type=[
                 "pdf", "docx", "doc", "txt", "rtf",
                 "odt", "html", "htm", "png", "jpg", "jpeg"
            ],
            help="PDF, Word, TXT, RTF, ODT, HTML and image formats. Maximum 5 MB.",
            key="candidate_resume_uploader",
            max_upload_size=5
)

        upload_submitted = st.button(
            "🚀 Upload & Extract Candidate Details",
            type="primary",
            use_container_width=True,
            key="upload_candidate_resume_button"
        )

    if upload_submitted:

        if uploaded_file is None:
            st.warning("Please select a supported resume file.")

        elif uploaded_file.size > 5 * 1024 * 1024:
            st.error("Resume size must not exceed 5 MB.")

        else:
            try:
                result = run_with_live_progress(
                    lambda: api.upload_candidate_resume(uploaded_file),
                    "Uploading resume and extracting candidate information...")
                
                st.session_state.uploaded_resume = result
                st.session_state.last_evaluation = None
                st.session_state.evaluation_thread_id = None

                st.success("Resume uploaded and processed successfully.")

            except Exception as error:
                show_error(error)

    # --------------------------------------------------
    # 02 - CANDIDATE INTELLIGENCE
    # --------------------------------------------------

    resume = st.session_state.get("uploaded_resume")

    if resume:

        st.markdown(
            '<div class="resume-gradient-line"></div>',
            unsafe_allow_html=True
        )

        st.markdown(
            '<div class="rainbow-title" '
            'style="font-size:27px;font-weight:800;">'
            '02 · Candidate Intelligence Profile</div>',
            unsafe_allow_html=True
        )

        st.caption(
            "Candidate information extracted from the uploaded resume. "
            "Verify extracted details against the original document."
        )

        profile_col1, profile_col2 = st.columns(2)

        with profile_col1:
            st.markdown(
                f"""
                <div class="resume-card">
                    <div class="resume-card-title">Candidate Name</div>
                    <div class="resume-card-value">
                        {html.escape(str(resume.get("full_name") or "Not detected"))}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

            st.markdown(
                f"""
                <div class="resume-card">
                    <div class="resume-card-title">Email Address</div>
                    <div class="resume-card-value">
                        {html.escape(str(resume.get("candidate_email") or "Not detected"))}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

        with profile_col2:
            st.markdown(
                f"""
                <div class="resume-card">
                    <div class="resume-card-title">Phone Number</div>
                    <div class="resume-card-value">
                        {html.escape(str(resume.get("phone") or "Not detected"))}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

            st.markdown(
                f"""
                <div class="resume-card">
                    <div class="resume-card-title">Location</div>
                    <div class="resume-card-value">
                        {html.escape(str(resume.get("location") or "Not detected"))}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

        # Resume metrics
        st.markdown("#### 📊 Resume Overview")

        metric1, metric2, metric3 = st.columns(3)

        metric1.metric(
            "Candidate ID",
            resume.get("candidate_id", "N/A")
        )

        metric2.metric(
            "Extracted Characters",
            f"{resume.get('extracted_text_length', 0):,}"
        )

        skills = resume.get("skills") or []

        metric3.metric(
            "Detected Skills",
            len(skills)
        )

        # Experience
        st.markdown("#### 💼 Experience")

        experience = resume.get("experience_years")

        if experience is not None:
            st.info(f"Detected experience: {experience} years")
        else:
            st.info(
                "Experience duration was not detected. "
                "This does not mean the candidate has no experience."
            )

        # Skills
        st.markdown("#### 🧠 Detected Technical Skills")

        if skills:
            skill_html = "".join(
                f'<span class="skill-tag">{html.escape(str(skill))}</span>'
                for skill in skills
            )

            st.markdown(
                f'<div style="line-height:2.8;">{skill_html}</div>',
                unsafe_allow_html=True
            )
        else:
            st.warning("No skills were detected in the uploaded resume.")

        # Education
        st.markdown("#### 🎓 Education")

        education = resume.get("education") or []

        if education:
            for item in education:
                st.markdown(
                    f"""
                    <div class="info-panel">
                        🎓 {html.escape(str(item))}
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        else:
            st.info("No education details were detected.")

        # Extracted text
        st.markdown("#### 📄 Extracted Resume Content")

        extracted_text = resume.get("extracted_text") or ""

        with st.expander(
            "View complete extracted resume text",
            expanded=False
        ):
            st.caption(
                f"{len(extracted_text):,} characters extracted"
            )

            st.text_area(
                "Resume content",
                value=extracted_text,
                height=350,
                disabled=True,
                label_visibility="collapsed",
                key=f"resume_text_preview_{resume.get('candidate_id', 'current')}"
            )

        # --------------------------------------------------
        # 03 - JOB DESCRIPTION AND EVALUATION
        # --------------------------------------------------
        st.markdown(
            '<div class="resume-gradient-line"></div>',
            unsafe_allow_html=True
        )

        st.markdown(
            '<div class="rainbow-title" '
            'style="font-size:27px;font-weight:800;">'
            '03 · Job Description Analysis</div>',
            unsafe_allow_html=True
        )

        st.caption(
            "Provide the target job description to evaluate "
            "candidate-job compatibility."
        )

        with st.form("job_description_form"):
            job_title = st.text_input(
                "Target Job Title",
                placeholder="Example: Junior Python Developer"
            )

            job_description = st.text_area(
                "Target Job Description",
                height=220,
                placeholder=(
                    "Enter required skills, responsibilities "
                    "and qualifications..."
                )
            )

            candidate_experience_years = st.number_input(
                "Candidate Experience (Years)",
                min_value=0.0,
                max_value=60.0,
                value=float(resume.get("experience_years") or 0.0),
                step=0.5
            )

            evaluate_submitted = st.form_submit_button(
                "🚀 Run AI Candidate Evaluation",
                type="primary",
                use_container_width=True
            )

        if evaluate_submitted:
            if not extracted_text:
                st.error("Please upload a candidate resume first.")

            elif not job_title.strip():
                st.error("Please enter the target job title.")

            elif not job_description.strip():
                st.error("Please enter the job description.")

            else:
                try:
                    result = run_with_live_progress(
                        lambda: api.evaluate_candidate(
                        resume_text=extracted_text,
                        job_title=job_title.strip(),
                        job_description=job_description.strip(),
                        candidate_experience_years=candidate_experience_years
                    ),
                    "Running Gemini and LangGraph recruitment evaluation..."
                )

                    if result:
                        st.session_state.last_evaluation = result
                        st.success("Candidate evaluation completed!")

                except Exception as error:
                    show_error(error)
       

    # --------------------------------------------------
    # 04 - AI EVALUATION REPORT
    # --------------------------------------------------

    result = st.session_state.get("last_evaluation")

    if result:

        st.markdown(
            '<div class="rainbow-line"></div>',
            unsafe_allow_html=True
        )

        st.markdown("### 04 · AI Evaluation Report")

        status = result.get("status", "unknown")
        analysis = result.get("analysis", {})

        st.info(f"Workflow status: {status}")

        if analysis:

            col1, col2, col3 = st.columns(3)

            col1.metric(
                "Skill Coverage",
                f"{analysis.get('match_percentage', 0)}%"
            )

            col2.metric(
                "Matched Skills",
                len(analysis.get("matched_skills", []))
            )

            col3.metric(
                "Skills Without Evidence",
                len(analysis.get("missing_skills", []))
            )

            st.subheader("Skill Comparison")

            left, right = st.columns(2)

            with left:
                st.markdown(
                    "#### <span style='color:#42e8a5'>✓ Matched Skills</span>",
                    unsafe_allow_html=True
                )

                display_list(
                    "Skills supported by resume evidence",
                    analysis.get("matched_skills", [])
                )

            with right:
                st.markdown(
                    "#### <span style='color:#ff9b9b'>! Missing Evidence</span>",
                    unsafe_allow_html=True
                )

                display_list(
                    "Skills without supplied resume evidence",
                    analysis.get("missing_skills", [])
                )

            st.subheader("AI Explanation")

            explanation = analysis.get("ai_explanation", {})

            if isinstance(explanation, dict):
                for key, value in explanation.items():
                    with st.expander(key.replace("_", " ").title()):
                        st.write(value)
            else:
                st.write(explanation)

            st.subheader("Evidence Details")

            with st.expander("Resume and job-description evidence"):
                st.write("**Resume evidence**")
                st.json(analysis.get("resume_skill_evidence", []))

                st.write("**Job description evidence**")
                st.json(analysis.get("job_skill_evidence", []))

            warnings = analysis.get("guardrail_warnings", [])

            if warnings:
                st.warning("Guardrail warnings")
                st.write(warnings)

            scoring_note = analysis.get("scoring_note")

            if scoring_note:
                st.caption(f"Scoring note: {scoring_note}")

            st.caption(
                "AI evaluation is decision support. "
                "Skill coverage is not a hiring recommendation."
            )

        # --------------------------------------------------
        # 05 - HUMAN REVIEW
        # --------------------------------------------------

        if status == "awaiting_human_review":

            st.markdown(
                '<div class="rainbow-line"></div>',
                unsafe_allow_html=True
            )

            st.markdown("### 05 · Recruiter Human Review")

            st.warning(
                "Human review is required before the workflow can continue."
            )

            with st.form("human_review_form"):

                decision = st.radio(
                    "Your review decision",
                    ["Approve review", "Do not approve"],
                    horizontal=True
                )

                comment = st.text_area(
                    "Reviewer comments",
                    placeholder="Enter your review observations..."
                )

                review_submitted = st.form_submit_button(
                    "Submit Review Decision",
                    type="primary",
                    use_container_width=True
                )

            
        if review_submitted:
            try:
                with st.spinner("Submitting recruiter decision..."):
                    review_result = api.approve_evaluation(
                        thread_id=result["thread_id"],
                        approved=(decision == "Approve review"),
                        comment=comment
                    )

                st.session_state.last_review_result = review_result
                st.session_state.last_review_decision = decision
                st.session_state.last_review_comment = comment

                status = str(
                    review_result.get("approval_status", "unknown")
                ).lower()

                is_approved = status == "approved"
                status_label = "APPROVED" if is_approved else "NOT APPROVED"
                status_color = "#34d399" if is_approved else "#fb7185"

                status_message = (
                    "The evaluation has been approved by the recruiter."
                    if is_approved
                    else "The evaluation was not approved by the recruiter."
                )

                reviewer_id = html.escape(
                    str(review_result.get("reviewer_id", "N/A"))
                )

                thread_id = html.escape(
                    str(review_result.get("thread_id", "N/A"))
                )

                safe_comment = html.escape(
                    str(comment or "No reviewer comments provided.")
                )

                st.markdown(
                    f"""
                    <div style="
                        background:linear-gradient(135deg,#102b35,#17243b);
                        border:1px solid {status_color};
                        border-radius:14px;
                        padding:22px;
                        margin-top:18px;
                    ">
                        <div style="
                            color:{status_color};
                            font-size:23px;
                            font-weight:800;
                        ">
                            ✓ REVIEW DECISION RECORDED
                        </div>
                        <div style="color:#cbd5e1;margin-top:7px;">
                            {status_message}
                        </div>
                        <div style="
                            color:{status_color};
                            font-size:27px;
                            font-weight:800;
                            margin-top:18px;
                        ">
                            {status_label}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                col1, col2 = st.columns(2)

                with col1:
                    st.metric("Reviewer ID", reviewer_id)

                with col2:
                    st.markdown(
                        f"**Decision**\n\n"
                        f"<span style='color:{status_color};"
                        f"font-weight:800'>{status_label}</span>",
                        unsafe_allow_html=True
                    )

                st.markdown(
                    f"""
                    <div style="
                        background:#101827;
                        border:1px solid #334155;
                        border-radius:11px;
                        padding:17px;
                        margin-top:13px;
                    ">
                        <div style="color:#c4b5fd;font-weight:700;">
                            REVIEWER COMMENTS
                        </div>
                        <div style="
                            color:#e2e8f0;
                            line-height:1.7;
                            margin-top:10px;
                        ">
                            {safe_comment}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                with st.expander("Workflow audit reference"):
                    st.code(thread_id)

                st.success("Recruiter review submission completed.")

                st.session_state.last_evaluation = None
                st.session_state.evaluation_thread_id = None

            except Exception as error:
                show_error(error)


# --------------------------------------------------
# JOB MANAGEMENT
# --------------------------------------------------

def jobs_page():

    page_header(
        "Job Management",
        "Explore and review available recruitment opportunities."
    )

    if st.button("↻ Refresh Jobs"):
        st.session_state.jobs_refresh = True

    try:
        with st.spinner("Loading jobs..."):
            result = api.get_jobs()

        jobs = (
            result
            if isinstance(result, list)
            else result.get("items", result.get("jobs", []))
        )

        if jobs:

            st.metric("Available Jobs", len(jobs))

            st.dataframe(
                jobs,
                use_container_width=True,
                hide_index=True
            )

        else:
            st.info("No jobs were returned by the API.")

    except Exception as error:
        show_error(error)


# --------------------------------------------------
# INTERVIEW INTELLIGENCE
# --------------------------------------------------

def interview_page():

    page_header(
        "Interview Intelligence",
        "Generate structured, job-relevant interview plans."
    )

    with st.form("interview_form"):

        title = st.text_input(
            "Job title",
            placeholder="e.g. Python Developer"
        )

        description = st.text_area(
            "Job description",
            height=180
        )

        skills_text = st.text_input(
            "Candidate skills",
            placeholder="Python, SQL, Machine Learning"
        )

        col1, col2 = st.columns(2)

        with col1:
            difficulty = st.selectbox(
                "Difficulty",
                ["beginner", "intermediate", "advanced"],
                index=1
            )

        with col2:
            question_count = st.slider(
                "Number of questions",
                min_value=5,
                max_value=20,
                value=10
            )

        submitted = st.form_submit_button(
            "Generate Interview Plan",
            type="primary",
            use_container_width=True
        )

    if submitted:

        if not title.strip():
            st.warning("Enter the job title.")

        elif len(description.strip()) < 50:
            st.warning(
                "Enter a job description containing at least 50 characters."
            )

        else:
            try:
                skills = [
                    item.strip()
                    for item in skills_text.split(",")
                    if item.strip()
                ]

                st.session_state.interview_result = None

                result = run_with_live_progress(
                    lambda: api.generate_interview(
                        title.strip(),
                        description.strip(),
                        skills,
                        difficulty,
                        question_count
                    ),
                    "Generating structured interview questions..."
                )

                st.session_state.interview_result = result

                guidance = result.get("evaluation_guidance", {})
                generation_method = guidance.get(
                    "generation_method",
                    "unknown"
                )

                if generation_method == "local_fallback":
                    st.warning(
                        "Gemini is currently unavailable. "
                        "A structured interview plan was generated "
                        "using AI HireMind's local fallback."
                    )
                else:
                    st.success("Gemini interview plan generated successfully.")

            except Exception as error:
                show_error(error)

    result = st.session_state.get("interview_result")

    if result:

        st.markdown(
            '<div class="rainbow-line"></div>',
            unsafe_allow_html=True
        )

        guidance = result.get("evaluation_guidance", {})

        generation_method = guidance.get(
            "generation_method",
            "unknown"
        )

        if generation_method == "local_fallback":
            st.warning(
                "LOCAL FALLBACK MODE — These questions were generated "
                "using Python templates, not Gemini."
            )

            st.caption(
                guidance.get("fallback_reason", "")
            )

        elif generation_method == "gemini":
            st.success("Generated using Gemini.")

        else:
            st.info("Interview plan generated.")

        st.subheader("Generated Interview Questions")

        questions = result.get("questions", [])

        st.metric("Questions Generated", len(questions))

        for index, question in enumerate(questions, start=1):

            with st.expander(
                f"{index}. {question.get('question', 'Interview Question')}"
            ):

                st.write(
                    "**Category:**",
                    question.get("category")
                )

                st.write(
                    "**Competency:**",
                    question.get("competency")
                )

                st.write(
                    "**Difficulty:**",
                    question.get("difficulty")
                )

                st.write("**What to look for:**")

                for item in question.get("what_to_look_for", []):
                    st.markdown(f"- {item}")

                st.write("**Follow-up questions:**")

                for item in question.get("follow_up_questions", []):
                    st.markdown(f"- {item}")

        st.subheader("Evaluation Rubric")

        st.write("**Assessment Focus**")

        for item in guidance.get("assessment_focus", []):
            st.markdown(f"- {item}")

        st.write("**Evaluation Method**")
        st.write(guidance.get("evaluation_method", "Not provided."))

        st.write("**Scoring Guidance**")
        st.write(guidance.get("scoring_guidance", "Not provided."))


# --------------------------------------------------
# RECRUITER MEMORY
# --------------------------------------------------

def memories_page():

    page_header(
        "Recruiter Memory",
        "Manage saved recruiter preferences and approved knowledge."
    )

    if "memories_loaded" not in st.session_state:
        st.session_state.memories_loaded = False

    st.markdown("### Save New Memory")

    with st.form("memory_form"):

        memory_type = st.selectbox(
            "Memory category",
            ["recruiter_preference", "approved_knowledge"]
        )

        memory_key = st.text_input(
            "Memory key",
            placeholder="e.g. preferred_python_skills"
        )

        memory_value_text = st.text_area(
            "Memory value (valid JSON)",
            value='{"preference": "Example preference"}',
            height=120
        )

        submitted = st.form_submit_button(
            "Save Memory",
            type="primary"
        )

    if submitted:

        if not memory_key.strip():
            st.warning("Enter a memory key.")

        else:
            try:
                value = json.loads(memory_value_text)

                if not isinstance(value, dict):
                    raise ValueError(
                        "Memory value must be a JSON object."
                    )

                api.save_memory(
                    memory_type,
                    memory_key.strip(),
                    value
                )

                st.session_state.memories = api.get_memories()
                st.session_state.memories_loaded = True

                st.success("Memory saved successfully.")
                st.rerun()

            except Exception as error:
                show_error(error)

    st.markdown(
        '<div class="rainbow-line"></div>',
        unsafe_allow_html=True
    )

    st.subheader("Saved Memories")

    if st.button("Load Memories", use_container_width=True):

        try:
            memories_result = api.get_memories()

            if isinstance(memories_result, list):
                memories = memories_result
            elif isinstance(memories_result, dict):
                memories = memories_result.get(
                    "memories",
                    memories_result.get("items", [])
                )
            else:
                memories = []

            st.session_state.memories = memories
            st.session_state.memories_loaded = True

            st.rerun()

        except Exception as error:
            show_error(error)

    memories = st.session_state.get("memories", [])

    if not memories:

        if st.session_state.memories_loaded:

            st.markdown(
                """
                <div style="
                    background:linear-gradient(135deg,#142b3b,#17243b);
                    border:1px solid #36cfa5;
                    border-radius:15px;
                    padding:25px;
                    margin-top:18px;
                    text-align:center;
                ">
                    <div style="font-size:38px;">🧠</div>
                    <h3 style="color:#42e8a5;">
                        Your memory is empty.
                    </h3>
                    <p style="color:#d4def5;">
                        No saved recruiter preferences found.
                        Add a new memory to personalize future AI evaluations.
                    </p>
                </div>
                """,
                unsafe_allow_html=True
            )

        else:
            st.info("Click Load Memories to retrieve your saved preferences.")

    else:

        st.success(f"{len(memories)} saved memory record(s) found.")

        for index, memory in enumerate(memories):

            memory_type = memory.get("memory_type", "")
            memory_key = memory.get("memory_key", "")

            with st.expander(
                f"{memory_type} — {memory_key}"
            ):

                st.json(memory.get("memory_value", {}))

                if st.button(
                    "Delete Memory",
                    key=f"delete_memory_{index}_{memory_key}"
                ):

                    try:
                        api.delete_memory(
                            memory_type,
                            memory_key
                        )

                        updated_result = api.get_memories()

                        if isinstance(updated_result, list):
                            updated_memories = updated_result
                        elif isinstance(updated_result, dict):
                            updated_memories = updated_result.get(
                                "memories",
                                updated_result.get("items", [])
                            )
                        else:
                            updated_memories = []

                        st.session_state.memories = updated_memories
                        st.session_state.memories_loaded = True

                        st.success("Memory deleted successfully.")
                        st.rerun()

                    except Exception as error:
                        show_error(error)

# --------------------------------------------------
# MAIN APPLICATION
# --------------------------------------------------

def main():

    # PUBLIC CAREERS PORTAL — no login required
    if st.query_params.get("careers") == "1":
        render_careers_portal(api)
        return

    # RECRUITER PORTAL — authentication required
    if not st.session_state.access_token:
        login_screen()
        return

    profile = st.session_state.user_profile or {}

    # Sidebar navigation
    with st.sidebar:

        st.markdown(
            '<h1 class="rainbow-title">🧠 AI HireMind</h1>',
            unsafe_allow_html=True
        )

        st.caption("Recruitment Intelligence Platform")

        st.markdown('<div class="rainbow-line"></div>',
                    unsafe_allow_html=True)

        st.markdown("### Recruiter Account")

        st.write(profile.get("email", ""))
        st.caption(
            f"Role: {profile.get('role', '').title()}"
        )

        st.divider()

        page = st.radio(
            "WORKSPACE",
            [
                "Dashboard",
                "AI Evaluation",
                "Job Management",
                "Interview Intelligence",
                "Recruiter Memory"
            ],
            label_visibility="visible"
        )

        st.divider()

        if st.button(
            "↪ Logout",
            use_container_width=True
        ):

            api.clear_token()

            st.session_state.access_token = None
            st.session_state.user_profile = None
            st.session_state.uploaded_resume = None
            st.session_state.last_evaluation = None
            st.session_state.interview_result = None
            st.session_state.evaluation_thread_id = None

            st.rerun()

        st.markdown(
            """
            <div style="
                position:relative;
                padding-top:20px;
                color:#8290aa;
                font-size:12px;
                text-align:center;">
                AI HireMind · Recruiter Workspace
            </div>
            """,
            unsafe_allow_html=True
        )

    # Page routing
    if page == "Dashboard":
        dashboard_page()

    elif page == "AI Evaluation":
        evaluation_page()

    elif page == "Job Management":
        jobs_page()

    elif page == "Interview Intelligence":
        interview_page()

    elif page == "Recruiter Memory":
        memories_page()


if __name__ == "__main__":
    main()
