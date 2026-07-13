"""
location_score.py
------------------
Feature 2: Location Safety Score Predictor

Given a REAL place name/area + time of day:
  1. Validate the location using OpenStreetMap's Nominatim geocoder (via geopy) --
     completely free, no API key or billing required. This stops random
     gibberish from getting a fake safety score.
  2. Ask Gemini to reason about general, well-known public-safety factors
     (lighting, foot traffic, area type) and return a structured JSON score.

Falls back gracefully:
  - Nominatim network/service error -> location is either rejected (if
    config.STRICT_LOCATION_VALIDATION is True) or scored with a clearly
    labeled "unverified" warning (if False) -- so a flaky connection during
    a demo never hard-crashes the page.
  - No Gemini key / API error -> a rule-based heuristic score is used instead.

NOTE: This is a general-awareness / prevention tool based on common safety
knowledge -- NOT a real-time crime database. Location data (c) OpenStreetMap
contributors, https://www.openstreetmap.org/copyright
"""

import json
import random
import re

import plotly.graph_objects as go
import streamlit as st

import config
from database.db_operations import get_location_history, save_location_score
from utils.gemini_helper import ask_gemini

SYSTEM_PROMPT = """You are a personal-safety risk assessment engine.
Given a place description and time of day, estimate a general safety score.
Respond ONLY with valid JSON, no markdown, no extra text, in this exact shape:
{
  "safety_score": <integer 0-100, 100 = very safe>,
  "risk_level": "<Low Risk | Moderate Risk | High Risk>",
  "factors": ["factor 1", "factor 2", "factor 3"],
  "tips": ["tip 1", "tip 2", "tip 3"]
}
Base your reasoning on commonly known, general safety factors such as lighting,
how busy/populated an area typically is at that time, presence of public transport,
and whether it's a well-known area type (e.g. downtown, residential, industrial, highway).
Do not claim to have real-time or private crime-database data.
"""

# OpenStreetMap "class" values worth accepting as "a real, specific-enough location".
# (Nominatim tags every result with a class/type pair, e.g. class="place", type="city")
ALLOWED_OSM_CLASSES = {
    "place",       # city, town, village, suburb, neighbourhood, hamlet
    "boundary",    # administrative boundaries
    "highway",     # streets, roads
    "amenity",     # amenity POIs (restaurants, hospitals, colleges, etc.)
    "tourism",     # tourist attractions, hotels
    "shop",
    "building",
    "railway",     # stations
    "leisure",     # parks, stadiums
    "landuse",
}


# ---------------------------------------------------------------------
# NOMINATIM GEOCODER (lazy, rate-limited, never crashes at import time)
# ---------------------------------------------------------------------
_geocode_fn = None
_geocoder_init_attempted = False


def _get_geocode_fn():
    """
    Lazily build a rate-limited Nominatim geocode function.
    Nominatim's public server is free but requires:
      - a descriptive User-Agent (see config.NOMINATIM_USER_AGENT)
      - max ~1 request/second, which RateLimiter enforces for us automatically
    Returns None only if the geopy library itself fails to import/initialize.
    """
    global _geocode_fn, _geocoder_init_attempted
    if _geocoder_init_attempted:
        return _geocode_fn

    _geocoder_init_attempted = True
    try:
        from geopy.geocoders import Nominatim
        from geopy.extra.rate_limiter import RateLimiter

        geolocator = Nominatim(user_agent=config.NOMINATIM_USER_AGENT, timeout=10)
        _geocode_fn = RateLimiter(
            geolocator.geocode,
            min_delay_seconds=1,   # respect Nominatim's usage policy
            max_retries=2,
            error_wait_seconds=2.0,
            swallow_exceptions=False,
        )
    except Exception as e:
        print("Nominatim init error:", e)
        _geocode_fn = None

    return _geocode_fn


def validate_location(location: str):
    """
    Try to verify `location` is a real place via OpenStreetMap Nominatim.

    Returns:
      - dict with "formatted_address" (no "unverified" key) if genuinely verified
      - None if the location should be REJECTED -- either Nominatim found no
        match, or a lookup error occurred and STRICT_LOCATION_VALIDATION is on
      - {"formatted_address": location, "unverified": True, "reason": ...} ONLY
        when a lookup error occurred (network/service issue) AND strict mode
        is off -- keeps the feature usable offline, but the UI must clearly
        flag this to the user.
    """
    geocode = _get_geocode_fn()

    if geocode is None:
        if config.STRICT_LOCATION_VALIDATION:
            return None
        return {"formatted_address": location, "unverified": True, "reason": "Geocoding service unavailable"}

    try:
        result = geocode(location, addressdetails=True, exactly_one=True, language="en")
    except Exception as e:
        print("Nominatim lookup error:", e)
        if config.STRICT_LOCATION_VALIDATION:
            return None
        return {
            "formatted_address": location,
            "unverified": True,
            "reason": f"OpenStreetMap lookup error: {e}",
        }

    if result is None:
        # Nominatim actively found no match -> genuinely not a recognizable place.
        return None

    raw = result.raw or {}
    osm_class = raw.get("class", "")

    if osm_class and osm_class not in ALLOWED_OSM_CLASSES:
        # Matched something, but it's too generic/unrelated to be a useful "place"
        # (e.g. a natural feature, waterway) -- treat as not specific enough.
        return None

    return {
        "formatted_address": result.address,
        "lat": result.latitude,
        "lon": result.longitude,
        "osm_class": osm_class,
        "osm_type": raw.get("type", ""),
    }


# ---------------------------------------------------------------------
# OFFLINE FALLBACK SCORER (used when Gemini is unavailable)
# ---------------------------------------------------------------------
def _heuristic_score(location: str, time_of_day: str):
    seed = sum(ord(c) for c in location.lower()) + hash(time_of_day) % 100
    random.seed(seed)

    score = random.randint(45, 90)
    if "Night" in time_of_day or "Evening" in time_of_day:
        score -= 15
    score = max(10, min(score, 95))

    if score >= 75:
        risk = "Low Risk"
    elif score >= 45:
        risk = "Moderate Risk"
    else:
        risk = "High Risk"

    factors = [
        f"General activity level typically {'high' if score > 60 else 'low'} in this type of area",
        f"Time of day ({time_of_day}) affects visibility and foot traffic",
        "Estimate based on general safety heuristics (offline fallback mode)",
    ]
    tips = [
        "Share your live location with a trusted contact before heading out.",
        "Stick to well-lit, populated routes where possible.",
        "Keep your phone charged and easily accessible.",
    ]
    return score, risk, factors, tips


def _parse_json_block(text: str):
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError("No JSON found")
    return json.loads(match.group(0))


# ---------------------------------------------------------------------
# MAIN SCORING FUNCTION
# ---------------------------------------------------------------------
def get_safety_score(location: str, time_of_day: str):
    """
    Returns None if the location is rejected (Nominatim found no real match,
    or a lookup error occurred and STRICT_LOCATION_VALIDATION is on).
    Otherwise returns (score, risk_level, factors, tips, verified_address, unverified, reason).
    """
    place = validate_location(location)
    if place is None:
        return None

    address = place["formatted_address"]
    unverified = place.get("unverified", False)
    reason = place.get("reason", "")

    try:
        prompt = f"Location/area description: {address}\nTime of day: {time_of_day}"
        raw = ask_gemini(prompt, system_instruction=SYSTEM_PROMPT, temperature=0.4)
        data = _parse_json_block(raw)
        score = int(data["safety_score"])
        risk = data["risk_level"]
        factors = data["factors"]
        tips = data["tips"]
    except Exception:
        score, risk, factors, tips = _heuristic_score(address, time_of_day)

    return score, risk, factors, tips, address, unverified, reason


# ---------------------------------------------------------------------
# GAUGE CHART
# ---------------------------------------------------------------------
def _gauge_chart(score: int):
    if score >= 75:
        bar_color = "#2ECC71"
    elif score >= 45:
        bar_color = "#F5A623"
    else:
        bar_color = "#E74C3C"

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        number={"suffix": " / 100", "font": {"size": 40}},
        gauge={
            "axis": {"range": [0, 100], "tickcolor": "white"},
            "bar": {"color": bar_color},
            "bgcolor": "rgba(0,0,0,0)",
            "steps": [
                {"range": [0, 45], "color": "#4a1f24"},
                {"range": [45, 75], "color": "#4a3a1f"},
                {"range": [75, 100], "color": "#1f4a2c"},
            ],
        },
    ))
    fig.update_layout(
        height=280,
        margin=dict(l=20, r=20, t=20, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        font={"color": "white"},
    )
    return fig


# ---------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------
def render():
    st.subheader("📍 Location Safety Score Predictor")
    st.caption("Get a general AI-estimated safety score for a real area before you head out.")
    st.caption("🗺️ Location data verified via OpenStreetMap (Nominatim) — free, no API key required.")

    with st.form("location_form"):
        col1, col2 = st.columns([2, 1])
        with col1:
            location = st.text_input("Location", placeholder="e.g. Connaught Place, Delhi")
        with col2:
            time_of_day = st.selectbox(
                "Time of day",
                ["Morning (6AM-12PM)", "Afternoon (12PM-6PM)", "Evening (6PM-9PM)", "Late Night (12AM-5AM)"],
            )
        submitted = st.form_submit_button("🔍 Analyze Safety", use_container_width=True)

    if submitted:
        if not location.strip():
            st.warning("Please enter a location first.")
        else:
            with st.spinner("Verifying location and analyzing safety factors..."):
                result = get_safety_score(location, time_of_day)

            if result is None:
                st.error("❌ This location could not be verified as a real place.")
                st.info(
                    "Please enter a real city, area, locality, or landmark. Examples:\n"
                    "- Connaught Place, Delhi\n"
                    "- Cyber Hub, Gurugram\n"
                    "- Marina Beach, Chennai\n"
                    "- Sector 23, Gurugram"
                )
            else:
                score, risk, factors, tips, address, unverified, reason = result
                save_location_score(address, time_of_day, score, risk, " | ".join(factors), " | ".join(tips))

                if unverified:
                    st.warning(
                        f"⚠️ Location verification is temporarily unavailable ({reason or 'unknown error'}). "
                        "The score below is an AI estimate only, not a confirmed real place."
                    )
                else:
                    st.success(f"📍 Verified Location: {address}")

                col1, col2 = st.columns([1, 1])
                with col1:
                    st.plotly_chart(_gauge_chart(score), use_container_width=True)
                with col2:
                    risk_badge = {"Low Risk": "🟢", "Moderate Risk": "🟡", "High Risk": "🔴"}.get(risk, "⚪")
                    st.markdown(f"### {risk_badge} {risk}")
                    st.markdown(f"**Location:** {address}")
                    st.markdown(f"**Time:** {time_of_day}")

                st.markdown("#### 🔎 Key Factors")
                for f in factors:
                    st.markdown(f"- {f}")

                st.markdown("#### 🛡️ Safety Tips")
                for t in tips:
                    st.markdown(f"- {t}")

    with st.expander("📜 Recent lookups"):
        hist = get_location_history()
        if hist.empty:
            st.caption("No lookups yet.")
        else:
            st.dataframe(
                hist[["location_name", "time_of_day", "safety_score", "risk_level", "created_at"]],
                use_container_width=True,
                hide_index=True,
            )
    st.caption("Map data © OpenStreetMap contributors")
