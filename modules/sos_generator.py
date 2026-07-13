"""
sos_generator.py
------------------
Feature 3: Emergency SOS Message Generator

Generates a clear, copy-paste-ready emergency message for trusted contacts,
based on a short situation description, location, and urgency level.
"""

import streamlit as st
from utils.gemini_helper import ask_gemini
from database.db_operations import (
    save_sos_message, get_sos_history,
    add_contact, get_contacts, delete_contact,
)

SYSTEM_PROMPT = """You write short, clear emergency messages sent to trusted contacts.
Rules:
- 3-5 sentences max.
- Must include: what's happening, where (if given), and a clear ask for help or a call-back.
- Tone matches the urgency level given.
- No hashtags, no emojis except at most one at the very start.
- Output ONLY the message text, nothing else.
"""


def _fallback_message(situation, location, urgency):
    urgency_line = {
        "🔴 Critical": "This is urgent — please call me or emergency services right now.",
        "🟠 Urgent": "Please call me back as soon as you can.",
        "🟡 Just checking in": "No huge rush, but please check in with me when you can.",
    }.get(urgency, "Please get in touch when you can.")

    loc = f" I'm currently near {location}." if location else ""
    return (f"🚨 I need help. {situation.strip().rstrip('.')}.{loc} "
            f"{urgency_line}")


def generate_sos_message(situation, location, urgency):
    try:
        prompt = (f"Situation: {situation}\nLocation: {location or 'not specified'}\n"
                  f"Urgency level: {urgency}\nWrite the emergency message now.")
        return ask_gemini(prompt, system_instruction=SYSTEM_PROMPT, temperature=0.5)
    except Exception:
        return _fallback_message(situation, location, urgency)


def render():
    st.subheader("🆘 Emergency SOS Message Generator")
    st.caption("Describe your situation and instantly generate a message to send to trusted contacts.")

    tab1, tab2 = st.tabs(["✏️ Generate Message", "👥 Trusted Contacts"])

    with tab1:
        situation = st.text_area(
            "What's happening?",
            placeholder="e.g. Someone is following me on my way home from the station",
            height=90,
        )
        location = st.text_input("Your current location (optional)", placeholder="e.g. Near 5th Ave & Main St")
        urgency = st.select_slider(
            "Urgency level",
            options=["🟡 Just checking in", "🟠 Urgent", "🔴 Critical"],
            value="🟠 Urgent",
        )

        if st.button("⚡ Generate SOS Message", type="primary", use_container_width=True):
            if not situation.strip():
                st.warning("Please describe your situation first.")
            else:
                with st.spinner("Drafting your message..."):
                    message = generate_sos_message(situation, location, urgency)
                save_sos_message(situation, location, message, urgency)
                st.session_state["last_sos_message"] = message

        if "last_sos_message" in st.session_state:
            st.divider()
            st.markdown("#### 📋 Your message")
            st.code(st.session_state["last_sos_message"], language=None)
            st.caption("Copy this and send it via SMS, WhatsApp, or your preferred app.")

            contacts_df = get_contacts()
            if not contacts_df.empty:
                st.markdown("**Send to:**")
                st.write(", ".join(contacts_df["name"].tolist()))
            else:
                st.info("Add trusted contacts in the 'Trusted Contacts' tab to speed this up next time.")

        with st.expander("📜 Message history"):
            hist = get_sos_history()
            if hist.empty:
                st.caption("No messages generated yet.")
            else:
                for _, row in hist.iterrows():
                    st.markdown(f"**{row['urgency_level']}** · _{row['created_at']}_")
                    st.code(row["generated_message"], language=None)

    with tab2:
        st.markdown("Keep a list of people who should be contacted in an emergency.")
        with st.form("add_contact_form", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            with c1:
                name = st.text_input("Name")
            with c2:
                phone = st.text_input("Phone number")
            with c3:
                relation = st.text_input("Relation", placeholder="e.g. Sister, Roommate")
            add = st.form_submit_button("➕ Add contact", use_container_width=True)

        if add:
            if name.strip() and phone.strip():
                add_contact(name.strip(), phone.strip(), relation.strip())
                st.success(f"Added {name} to trusted contacts.")
                st.rerun()
            else:
                st.warning("Name and phone are required.")

        contacts_df = get_contacts()
        if contacts_df.empty:
            st.info("No trusted contacts added yet.")
        else:
            for _, row in contacts_df.iterrows():
                c1, c2 = st.columns([5, 1])
                with c1:
                    st.markdown(f"**{row['name']}** ({row['relation'] or 'Contact'}) — {row['phone']}")
                with c2:
                    if st.button("🗑️", key=f"del_contact_{row['id']}"):
                        delete_contact(row["id"])
                        st.rerun()
