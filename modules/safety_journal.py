"""
safety_journal.py
-------------------
Feature 5: Safety Journal with AI Insights

Lets the user privately log moments/situations related to how safe they felt.
Each entry gets a short AI-generated insight. Over time, an aggregate
"pattern insight" surfaces recurring themes (e.g. a specific route, time,
or person that keeps coming up) so the user can make informed decisions.
"""

import streamlit as st
from utils.gemini_helper import ask_gemini
from database.db_operations import add_journal_entry, get_journal_entries, delete_journal_entry

MOODS = ["😊 Felt Safe", "😐 Neutral", "😟 Uneasy", "😨 Unsafe"]

ENTRY_SYSTEM_PROMPT = """You are a supportive safety journal assistant.
Given one journal entry about how someone felt in a situation, respond with ONE short,
validating, practical insight (max 2 sentences). Be warm, not clinical. Do not diagnose
or make assumptions about the person's mental state -- focus only on the situation described."""

PATTERN_SYSTEM_PROMPT = """You analyze a list of personal safety journal entries and identify
recurring PATTERNS only (places, times, situations that repeat) -- not psychological judgments
about the person. Respond with 3-5 short bullet points, each starting with '- '. If entries are
too few or varied to find a pattern, say so briefly."""


def _fallback_insight(mood: str) -> str:
    return {
        "😊 Felt Safe": "Glad you felt safe — noting what made it feel that way can help you recognize good patterns.",
        "😐 Neutral": "A neutral moment logged — these small notes add up to a clearer safety picture over time.",
        "😟 Uneasy": "Thanks for logging this. Trusting that uneasy feeling is a good instinct — consider what specifically triggered it.",
        "😨 Unsafe": "This sounds tough. If you're ever in immediate danger, please contact local emergency services first.",
    }.get(mood, "Entry saved. Reflecting on these moments can help you spot patterns over time.")


def get_entry_insight(entry_text: str, mood: str) -> str:
    try:
        prompt = f"Mood: {mood}\nEntry: {entry_text}"
        return ask_gemini(prompt, system_instruction=ENTRY_SYSTEM_PROMPT, temperature=0.6)
    except Exception:
        return _fallback_insight(mood)


def get_pattern_insight(entries_df) -> str:
    if len(entries_df) < 3:
        return "Log a few more entries to unlock pattern detection across time, place, and mood."
    combined = "\n".join(
        f"- ({row['mood']}) {row['entry_text']}" for _, row in entries_df.iterrows()
    )
    try:
        return ask_gemini(combined, system_instruction=PATTERN_SYSTEM_PROMPT, temperature=0.5)
    except Exception:
        moods = entries_df["mood"].value_counts()
        top_mood = moods.idxmax()
        return f"- Most common mood logged: {top_mood} ({moods.max()} entries)\n- Add more detail to entries for richer AI pattern detection."


def render():
    st.subheader("📔 Safety Journal")
    st.caption("A private space to log how situations made you feel. AI adds a short insight to each entry.")

    with st.form("journal_form", clear_on_submit=True):
        entry_text = st.text_area(
            "What happened?",
            placeholder="e.g. Walked home late from the office, felt a bit on edge near the parking garage.",
            height=100,
        )
        mood = st.select_slider("How did it feel?", options=MOODS, value=MOODS[1])
        submitted = st.form_submit_button("💾 Save entry", use_container_width=True)

    if submitted:
        if not entry_text.strip():
            st.warning("Please write something first.")
        else:
            with st.spinner("Reflecting..."):
                insight = get_entry_insight(entry_text, mood)
            add_journal_entry(entry_text, mood, insight)
            st.success("Entry saved.")
            st.rerun()

    st.divider()
    entries_df = get_journal_entries()

    if not entries_df.empty:
        with st.expander("🧠 AI Pattern Insight (across all entries)", expanded=True):
            with st.spinner("Looking for patterns..."):
                pattern = get_pattern_insight(entries_df)
            st.markdown(pattern)

        mood_counts = entries_df["mood"].value_counts()
        cols = st.columns(len(mood_counts))
        for col, (mood_label, count) in zip(cols, mood_counts.items()):
            col.metric(mood_label, count)

    st.markdown("#### 📖 Past entries")
    if entries_df.empty:
        st.info("No journal entries yet. Your first entry will appear here.")
    else:
        for _, row in entries_df.iterrows():
            with st.container(border=True):
                c1, c2 = st.columns([5, 1])
                with c1:
                    st.markdown(f"**{row['mood']}** · _{row['created_at']}_")
                    st.write(row["entry_text"])
                    st.caption(f"✨ {row['ai_insight']}")
                with c2:
                    if st.button("🗑️", key=f"del_journal_{row['id']}"):
                        delete_journal_entry(row["id"])
                        st.rerun()
