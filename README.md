# 🛡️ SafeHer AI

**An AI-powered personal safety companion focused on prevention and emergency support.**

> Five tools for the moments before, during, and after feeling unsafe — a safety score
> before you go, a script if you need to leave, and a message ready the instant you need help.

**Live Demo:** https://safeher-ai.streamlit.app/                                                


**Demo Video:** https://drive.google.com/file/d/1r0iwQgdMYkISh_u2dIG5iYzM495T5qjL/view?usp=drive_link                                      
---

## Team:
|Anushka Sharma |

---

## Features

| # | Feature | What it does |
|---|---------|---------------|
| 1 |  **AI Safety Chatbot** | A conversational assistant tuned specifically for safety Q&A — de-escalation tips, safety planning, and calm support. |
| 2 |  **Location Safety Score Predictor** | Enter any *real* area + time of day → get an AI-estimated safety score (0-100), risk level, key factors, and tailored tips. Locations are verified for free via **OpenStreetMap (Nominatim)** — no API key or billing needed. |
| 3 |  **Emergency SOS Message Generator** | Describe a situation → instantly get a clear, ready-to-send emergency message for your trusted contacts. |
| 4 |  **Fake Call Simulator** | Trigger a realistic incoming call (with a believable AI-generated script) to help exit an uncomfortable situation. |
| 5 |  **Safety Journal with AI Insights** | Privately log how situations felt; get a short AI insight per entry plus long-term pattern detection across entries. |

Every AI feature has a **graceful offline fallback** — if there's no internet or API key during
judging, the app keeps working with smart rule-based responses instead of crashing.

## Tech Stack

- **Python 3.10+**
- **Streamlit** — UI framework
- **SQLite** — local, lightweight database (no server setup needed)
- **Gemini API** (`google-generativeai`) — the AI brain behind every feature
- **OpenStreetMap Nominatim** (via `geopy`) — free location verification, no API key
- **Plotly** — the animated safety-score gauge chart
- **Pandas** — data handling for history views

## Folder Structure

```
safeher_ai/
├── app.py                     # Main entry point — navigation & routing only
├── config.py                  # All app-wide settings & API key handling
├── requirements.txt
├── .env.example                # Copy to .env and add your Gemini key
├── .streamlit/
│   └── config.toml            # Custom dark theme colors
├── assets/
│   └── style.css               # Custom "Night Instrument Panel" design system
├── data/
│   └── safeher.db              # SQLite database (auto-created on first run)
├── database/
│   ├── db_setup.py             # Table creation / schema
│   └── db_operations.py        # All CRUD queries (single source of truth)
├── modules/                    # One file per feature — fully independent
│   ├── chatbot.py
│   ├── location_score.py
│   ├── sos_generator.py
│   ├── fake_call.py
│   └── safety_journal.py
└── utils/
    └── gemini_helper.py        # Single wrapper around the Gemini API
```

## Database Schema

SQLite database at `data/safeher.db`, created automatically on first run.

```sql
chat_history      (id, role, message, created_at)
location_scores   (id, location_name, time_of_day, safety_score, risk_level, factors, tips, created_at)
sos_contacts      (id, name, phone, relation, created_at)
sos_messages      (id, situation, location_text, generated_message, urgency_level, created_at)
journal_entries   (id, entry_text, mood, ai_insight, created_at)
```

## Project Setup

```bash
# 1. Clone the repository
git clone https://github.com/<your-username>/safeher-ai.git
cd safeher-ai

# 2. (Recommended) create a virtual environment
python -m venv .venv
.venv\Scripts\activate      # Windows
source .venv/bin/activate   # macOS/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Add your Gemini API key
cp .env.example .env
# then open .env and paste your key:
# GEMINI_API_KEY=your_actual_key_here

# 5. Run the app
streamlit run app.py
```

The app opens at `http://localhost:8501`. No Gemini key? No problem — SafeHer AI
automatically switches to **offline demo mode** with smart fallback responses so every
feature still works. Location verification needs **no key at all** (OpenStreetMap is free).

## How It Works (Architecture)

1. **`database/`** — where data lives. `db_setup.py` builds the tables once; `db_operations.py`
   is the only place allowed to touch them, so every query is in one auditable spot.
2. **`utils/gemini_helper.py`** — one small file whose only job is "send this text to Gemini,
   get text back." If Gemini can't be reached, it raises a clear error every feature already
   knows how to handle gracefully.
3. **`modules/`** — each feature is its own file with a `render()` function. `app.py` calls the
   right one depending on the sidebar selection.
4. **`app.py`** — the only file that runs first: page setup, sidebar, routing. No feature logic
   lives here on purpose, to keep it short and readable.

**Why fallbacks everywhere?** Hackathon WiFi is unreliable and API keys expire. Every AI or
network call is wrapped so the app degrades gracefully instead of crashing mid-demo.

## How This Maps to the Judging Criteria

- **Innovation** — combines prevention (verified location score, journal insights) *and*
  real-time emergency support (SOS generator, fake call) in one cohesive companion, not a
  single chatbot wrapper. Location claims are actually checked against OpenStreetMap instead
  of trusting free-text input.
- **Practical Use** — every feature solves a real, everyday safety need with zero setup
  friction (no paid APIs, no account creation).
- **UI/UX** — a deliberately designed "Night Instrument Panel" identity (dusk palette, a
  signature pulsing "beacon" status indicator, Space Grotesk/Inter/IBM Plex Mono type system)
  built for this specific subject, not a default template look.
- **Technical Implementation** — clean modular architecture, persistent SQLite storage,
  structured JSON prompting for reliable AI output, free geocoding validation, and offline-safe
  fallbacks throughout.
- **Presentation** — a polished home dashboard, live system-status readout, clear README, and
  beginner-friendly code comments make this easy to demo and easy to extend.

## Future Scope

- Real-time GPS tracking + live location sharing with contacts
- Integration with actual emergency services APIs (where available per region)
- Voice-activated SOS trigger ("Hey SafeHer, help")
- Community-sourced, verified area safety reports
- Native mobile app (React Native / Flutter) wrapping the same backend logic

## Disclaimer

SafeHer AI is a hackathon prototype for **educational and demonstration purposes**. It is not a
certified emergency service and should never replace calling local emergency services (911 / 112
/ 100, etc.) in a real emergency. Location data © OpenStreetMap contributors.

---

Built with for safer streets, smarter tech.
