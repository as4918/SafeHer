"""
chatbot.py
----------
Feature 1: AI Safety Chatbot

A conversational assistant with a system prompt tuned specifically for
personal-safety Q&A -- de-escalation advice, safety planning, legal helpline
info, and calm emotional support. Not a generic chatbot.
"""

import streamlit as st
from utils.gemini_helper import ask_gemini
from database.db_operations import save_chat_message, get_chat_history, clear_chat_history

SYSTEM_PROMPT = """You are SafeHer AI, a calm, empathetic personal-safety assistant.
Your job: help the user think through personal safety situations, give practical
prevention tips, de-escalation advice, and point them to real emergency resources.
Rules:
- Keep answers short (3-6 sentences) and practical, like a knowledgeable friend, not a legal document.
- If the user describes an emergency in progress, your FIRST line must tell them to
  contact local emergency services (e.g. 911 / 112 / 100 depending on country) immediately.
- Never be preachy. Be warm, direct, and actionable.
- You are not a replacement for police, medical, or legal professionals -- say so only when relevant.
"""

FALLBACK_RESPONSES = {
    "default": "I'm here for you. While I can't reach the AI service right now, here's a general tip: "
                "trust your instincts -- if a situation feels wrong, it probably is. Move to a public, "
                "well-lit area, and call someone you trust or local emergency services if you feel unsafe.",
    "walking alone": "When walking alone: stay in well-lit, populated areas, keep your phone charged, "
                      "share your live location with a trusted contact, and walk confidently and alert.",
    "stalker": "If you believe you're being followed: head to the nearest open business or crowded area, "
               "call someone on the phone (even if just talking), and contact local police once you're safe.",
}


def _fallback_reply(user_message: str) -> str:
    msg = user_message.lower()
    for key, reply in FALLBACK_RESPONSES.items():
        if key != "default" and key in msg:
            return reply
    return FALLBACK_RESPONSES["default"]


def get_bot_reply(user_message: str) -> str:
    try:
        return ask_gemini(user_message, system_instruction=SYSTEM_PROMPT, temperature=0.6)
    except Exception:
        return _fallback_reply(user_message)


def render():
    st.subheader("💬 AI Safety Chatbot")
    st.caption("Ask about safety tips, how to handle a situation, or just talk it through.")

    history_df = get_chat_history()

    chat_container = st.container(height=420)
    with chat_container:
        if history_df.empty:
            st.info("👋 Hi, I'm SafeHer AI. Ask me anything about staying safe — "
                     "e.g. *'What should I do if someone is following me?'*")
        for _, row in history_df.iterrows():
            with st.chat_message("user" if row["role"] == "user" else "assistant",
                                  avatar="🧑" if row["role"] == "user" else "🛡️"):
                st.write(row["message"])

    col1, col2 = st.columns([5, 1])
    user_input = st.chat_input("Type your message...")

    with col2:
        if st.button("🗑️ Clear", use_container_width=True):
            clear_chat_history()
            st.rerun()

    if user_input:
        save_chat_message("user", user_input)
        with st.spinner("SafeHer AI is thinking..."):
            reply = get_bot_reply(user_input)
        save_chat_message("assistant", reply)
        st.rerun()

    with st.expander("💡 Quick prompts"):
        quick_prompts = [
            "What should I do if someone is following me?",
            "Tips for walking alone at night",
            "How do I set up an emergency contact plan?",
            "What should I keep in a safety kit?",
        ]
        for qp in quick_prompts:
            if st.button(qp, key=f"qp_{qp}"):
                save_chat_message("user", qp)
                with st.spinner("SafeHer AI is thinking..."):
                    reply = get_bot_reply(qp)
                save_chat_message("assistant", reply)
                st.rerun()
