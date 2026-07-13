"""
fake_call.py
------------
Feature 4: Fake Call Simulator

Simulates a realistic incoming call screen with a countdown, so a user can
create a believable excuse to leave an uncomfortable situation. Also
generates a short "what they might say" script preview using Gemini, so the
user can mentally rehearse the fake conversation.
"""

import time
import streamlit as st
from utils.gemini_helper import ask_gemini

SYSTEM_PROMPT = """Write a short, natural one-sided phone call script (what the CALLER would say,
in 4-5 short lines) for someone pretending an urgent situation exists so the person receiving the
call has a believable reason to leave where they are. Keep it casual and realistic, like a friend
or family member calling. Output only the lines, one per line, no labels."""

FALLBACK_SCRIPT = [
    "Hey! Where are you, everything okay?",
    "Actually, can you come get me? Something came up.",
    "I'm sorry to ask, it's kind of urgent.",
    "Okay great, see you in a few minutes. Thank you!",
]

CALLER_PRESETS = ["Mom 📱", "Dad 📱", "Roommate 🏠", "Best Friend 💕", "Work - Boss 💼"]


def generate_script(caller_name: str):
    try:
        prompt = f"The caller is: {caller_name}"
        raw = ask_gemini(prompt, system_instruction=SYSTEM_PROMPT, temperature=0.8)
        lines = [l.strip("- ").strip() for l in raw.split("\n") if l.strip()]
        return lines[:6] if lines else FALLBACK_SCRIPT
    except Exception:
        return FALLBACK_SCRIPT


def render():
    st.subheader("📞 Fake Call Simulator")
    st.caption("Trigger a realistic incoming call to help you exit an uncomfortable situation.")

    if "call_active" not in st.session_state:
        st.session_state.call_active = False
    if "call_script" not in st.session_state:
        st.session_state.call_script = []

    if not st.session_state.call_active:
        col1, col2 = st.columns(2)
        with col1:
            caller = st.selectbox("Choose caller", CALLER_PRESETS)
        with col2:
            delay = st.selectbox("Ring in...", ["Now", "10 seconds", "30 seconds", "1 minute"], index=0)

        if st.button("📲 Trigger Fake Call", type="primary", use_container_width=True):
            if delay != "Now":
                secs = {"10 seconds": 10, "30 seconds": 30, "1 minute": 60}[delay]
                with st.spinner(f"Call from {caller} incoming in {delay}..."):
                    time.sleep(min(secs, 5))  # capped for demo purposes
            st.session_state.call_active = True
            st.session_state.caller_name = caller
            st.session_state.call_script = generate_script(caller)
            st.rerun()

        st.info("💡 Tip: set a delay, then casually put your phone away — it'll 'ring' right on cue.")

    else:
        caller = st.session_state.get("caller_name", "Unknown")
        st.markdown(
            f"""
            <div style="text-align:center; padding: 30px; border-radius: 20px;
                        background: linear-gradient(135deg, #2b1055, #7597de); color:white;">
                <p style="font-size:16px; opacity:0.8; margin-bottom:0;">Incoming call</p>
                <h1 style="font-size:42px; margin:10px 0;">📱 {caller}</h1>
                <p style="opacity:0.7;">mobile</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.write("")
        c1, c2 = st.columns(2)
        with c1:
            answer = st.button("🟢 Answer", use_container_width=True)
        with c2:
            decline = st.button("🔴 Decline", use_container_width=True)

        if answer:
            st.markdown("#### 🗣️ Suggested script (say these out loud)")
            for i, line in enumerate(st.session_state.call_script, 1):
                st.markdown(f"**{i}.** {line}")
            st.success("Use this as your cue to excuse yourself and leave the situation.")

        if answer or decline:
            if st.button("End call / Reset"):
                st.session_state.call_active = False
                st.rerun()
