"""
app.py
------
Main entry point for SafeHer AI.

Run with:  streamlit run app.py

Responsibilities of this file ONLY:
  1. Page config + custom CSS injection
  2. Database initialization
  3. Sidebar navigation
  4. Routing to the correct feature module

All feature logic lives in modules/*.py -- this keeps app.py short and readable.
"""

import streamlit as st

import config
from database.db_setup import init_database
from modules import chatbot, location_score, sos_generator, fake_call, safety_journal


# ------------------------------------------------------------------
# PAGE CONFIG (must be the first Streamlit call)
# ------------------------------------------------------------------
st.set_page_config(
    page_title=config.APP_NAME,
    page_icon=config.APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
)


# ------------------------------------------------------------------
# INIT
# ------------------------------------------------------------------
init_database()

with open("assets/style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


# ------------------------------------------------------------------
# SIDEBAR NAVIGATION
# ------------------------------------------------------------------
PAGES = {
    "Home": "home",
    "AI Safety Chatbot": "chatbot",
    "Location Safety Score": "location",
    "SOS Message Generator": "sos",
    "Fake Call Simulator": "fakecall",
    "Safety Journal": "journal",
}

with st.sidebar:
    beacon_class = "" if not config.DEMO_MODE else "offline"
    st.markdown(
        f"""
        <div class="sidebar-brand">
            <div class="mark-row">
                <span class="beacon-dot {beacon_class}"></span>
                <h2>{config.APP_NAME}</h2>
            </div>
           <p class="tagline">AI-powered Personal Safety Companion</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    choice = st.radio("Navigate", list(PAGES.keys()), label_visibility="collapsed")

    st.divider()
    if config.DEMO_MODE:
        st.warning("⚠️ Running in **offline demo mode** — add a Gemini API key in `.env` "
                   "for live AI responses. All features still work with smart fallbacks.")
    else:
        st.success("🟢 AI connected")

    st.caption("Built for hackathon demo purposes. Not a substitute for emergency services.")


# ------------------------------------------------------------------
# HERO HEADER
# ------------------------------------------------------------------
st.markdown(
    f"""
    <div class="safeher-hero">
        <div class="eyebrow"><span class="beacon-dot"></span> ALWAYS-ON SAFETY COMPANION</div>
        <h1>{config.APP_NAME}</h1>
        <p class="thesis">Five AI tools for the moments before, during, and after
        feeling unsafe — a safety score before you go, a script if you need
        to leave, and a message ready the instant you need help.</p>
    </div>
    """,
    unsafe_allow_html=True,
)


# ------------------------------------------------------------------
# ROUTING
# ------------------------------------------------------------------
page = PAGES[choice]

if page == "home":
    TILES = [
        ("CHAT","","AI Safety Chatbot",
         "Talk through a situation and get calm, practical safety guidance in real time."),
        ("SCORE","","Location Safety Score",
         "A verified, AI-estimated safety score and tips for any real area, before you head out."),
        ("SOS","","SOS Message Generator",
         "Instantly draft a clear emergency message ready to send to trusted contacts."),
        ("CALL","","Fake Call Simulator",
         "Trigger a realistic incoming call, with a script, to exit an uncomfortable situation."),
        ("JOURNAL", "","Safety Journal",
         "Privately log how situations felt and surface AI-detected patterns over time."),
    ]

    cols = st.columns(len(TILES))
    for col, (tag, icon, title, desc) in zip(cols, TILES):
        with col:
            st.markdown(
                f"""
                <div class="tile">
                    <span class="tag">{tag}</span>
                    <p class="tile-icon">{icon.upper()}</p>
                    <p class="tile-title">{title}</p>
                    <p class="tile-desc">{desc}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

    gemini_dot = "" if not config.DEMO_MODE else "offline"
    st.markdown(
        f"""
        <div class="status-bar">
            <div class="status-item"><span class="beacon-dot {gemini_dot}"></span>
                GEMINI AI &nbsp;{'CONNECTED' if not config.DEMO_MODE else 'OFFLINE — FALLBACK MODE'}</div>
            <div class="status-item"><span class="beacon-dot"></span>
                LOCATION VERIFICATION &nbsp;OPENSTREETMAP · NO API KEY</div>
            <div class="status-item"><span class="beacon-dot"></span>
                STORAGE &nbsp;LOCAL SQLITE · PRIVATE</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

elif page == "chatbot":
    chatbot.render()
elif page == "location":
    location_score.render()
elif page == "sos":
    sos_generator.render()
elif page == "fakecall":
    fake_call.render()
elif page == "journal":
    safety_journal.render()

st.markdown(
    '<div class="safeher-footer">SafeHer AI · Built with Python, Streamlit, SQLite & Gemini API '
    '· Hackathon Project</div>',
    unsafe_allow_html=True,
)
