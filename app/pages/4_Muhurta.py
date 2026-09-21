from __future__ import annotations

import calendar

import streamlit as st

from api_client import get_health, post_json
from config import MUHURTA_TIMEOUT, api_url
from constants import MONTH_NAMES, MUHURTA_PURPOSES, NAKSHATRAS
from muhurta_i18n import format_local_window, panchanga_flags, t, tithi_label
from state import init_state

st.set_page_config(page_title="Muhūrta Intelligence", layout="wide")
init_state()

health = get_health()
api_ok = health is not None and health.get("status") == "ok"
ephemeris_ok = bool(health and health.get("ephemeris_path_set"))
rag_ok = bool(health and health.get("rag_configured"))
gemini_ok = bool(health and health.get("gemini_configured"))

language_label = st.sidebar.radio("Language / Idioma", ["English", "Español"], index=1)
language = "es" if language_label == "Español" else "en"

st.title(t(language, "page_title"))
st.caption(t(language, "subtitle"))

with st.sidebar:
    st.subheader("API")
    st.caption(api_url())
    st.write("Status:", "ok" if api_ok else "unreachable")
    st.write("Ephemeris:", "ready" if ephemeris_ok else "not configured")
    st.write("RAG:", "ready" if rag_ok else "not configured")
    st.write("Gemini:", "ready" if gemini_ok else "not configured")

city_q = st.text_input(t(language, "city"), value="Madrid")
if st.button(t(language, "search_city")):
    places = post_json("/v1/muhurta/places/autocomplete", {"query": city_q}, timeout=30)
    if places:
        st.session_state.muhurta_places = places
        st.session_state.muhurta_geocode = []
    else:
        hits = post_json("/v1/muhurta/geocode", {"query": city_q}, timeout=30)
        st.session_state.muhurta_geocode = hits or []
        st.session_state.muhurta_places = []

places = st.session_state.get("muhurta_places") or []
hits = st.session_state.get("muhurta_geocode") or []
if places:
    labels = [item.get("label") or item.get("main_text") for item in places]
    chosen_label = st.selectbox(" ", labels, label_visibility="collapsed")
    suggestion = next(
        item for item in places if (item.get("label") or item.get("main_text")) == chosen_label
    )
    current = st.session_state.get("muhurta_location") or {}
    if current.get("place_id") != suggestion.get("place_id"):
        details = post_json(
            "/v1/muhurta/places/details",
            {"place_id": suggestion["place_id"]},
            timeout=30,
        )
        if details:
            st.session_state.muhurta_location = details
elif hits:
    labels = [item.get("label") or item.get("city") for item in hits]
    chosen = st.selectbox(" ", labels, label_visibility="collapsed")
    st.session_state.muhurta_location = next(
        item for item in hits if (item.get("label") or item.get("city")) == chosen
    )

location = st.session_state.get("muhurta_location")
if location:
    st.caption(
        f"{location.get('city')}, {location.get('country')} · "
        f"{location.get('latitude')}, {location.get('longitude')} · {location.get('timezone')}"
    )

purpose_labels = [item[2] if language == "es" else item[1] for item in MUHURTA_PURPOSES]
purpose_index = st.selectbox(
    t(language, "purpose"),
    range(len(MUHURTA_PURPOSES)),
    format_func=lambda i: purpose_labels[i],
    index=2,
)
purpose_id = MUHURTA_PURPOSES[purpose_index][0]
purpose_text = ""
if purpose_id == "custom":
    purpose_text = st.text_input(t(language, "custom_purpose"), value="")

natal = st.selectbox(t(language, "natal_nakshatra"), NAKSHATRAS, index=NAKSHATRAS.index("Anuradha"))

col_m, col_y = st.columns(2)
with col_m:
    month_name = st.selectbox(t(language, "month"), MONTH_NAMES, index=9)
    month = MONTH_NAMES.index(month_name) + 1
with col_y:
    year = st.number_input(t(language, "year"), min_value=1900, max_value=2100, value=2026, step=1)

start_hour, end_hour = st.slider(
    t(language, "hours_range"),
    min_value=0,
    max_value=23,
    value=(6, 18),
    format="%02d:00",
    help=t(language, "hours_range_help"),
)
st.caption(t(language, "hours_range_caption").format(start=start_hour, end=end_hour))
excluded = [hour for hour in range(24) if hour < start_hour or hour > end_hour]

last_day = calendar.monthrange(int(year), int(month))[1]
start_day, end_day = st.slider(
    t(language, "days_range"),
    min_value=1,
    max_value=last_day,
    value=(1, last_day),
    key=f"muhurta_days_{int(year)}_{int(month)}",
    help=t(language, "days_range_help"),
)
st.caption(
    t(language, "days_range_caption").format(
        start=start_day,
        end=end_day,
        month=month_name,
    )
)

with st.expander(t(language, "advanced")):
    preferred = st.multiselect(t(language, "preferred_hours"), list(range(start_hour, end_hour + 1)))
    min_duration = st.number_input("Minimum duration (minutes)", min_value=1, max_value=240, value=15)
    top_n = st.number_input("Number of results", min_value=1, max_value=12, value=5)

st.divider()
st.subheader(t(language, "step1"))
generate_disabled = not ephemeris_ok
if generate_disabled:
    st.info("Ephemeris is not configured.")

if st.button(t(language, "go"), type="primary", disabled=generate_disabled):
    st.session_state.muhurta_interpretation = None
    st.session_state.muhurta_selected_rank = 1
    chosen = st.session_state.get("muhurta_location")
    if chosen is None and city_q.strip():
        hits = post_json("/v1/muhurta/geocode", {"query": city_q}, timeout=30) or []
        st.session_state.muhurta_geocode = hits
        chosen = hits[0] if hits else None
        st.session_state.muhurta_location = chosen
    if chosen is None:
        st.error(t(language, "location_needed"))
    else:
        payload = {
            "purpose_id": purpose_id,
            "purpose_text": purpose_text or None,
            "natal_nakshatra": natal,
            "participants": [{"role": "beneficiary", "nakshatra": natal}],
            "location": {
                "city": chosen["city"],
                "country": chosen.get("country") or "",
                "latitude": chosen["latitude"],
                "longitude": chosen["longitude"],
                "timezone": chosen["timezone"],
            },
            "year": int(year),
            "month": int(month),
            "start_day": int(start_day),
            "end_day": int(end_day),
            "language": language,
            "advanced": {
                "preferred_hours": preferred,
                "excluded_hours": excluded,
                "minimum_duration_minutes": int(min_duration),
                "top_results": int(top_n),
            },
        }
        with st.spinner(t(language, "preparing")):
            result = post_json("/v1/muhurta/search", payload, timeout=MUHURTA_TIMEOUT)
            st.session_state.muhurta_result = result

result = st.session_state.get("muhurta_result")
if result:
    st.success(t(language, "ready"))
    stats = result.get("scan_stats") or {}
    if stats:
        st.caption(
            f"Samples {stats.get('samples')} · hard-filtered {stats.get('hard_filtered')} · "
            f"Lagna evaluations {stats.get('lagna_evaluations')} · "
            f"RAG embeddings {stats.get('embedding_calls')}"
        )
    profile = result.get("profile") or {}
    if profile:
        st.caption(
            f"Kārya-bhāva {profile.get('karya_bhava')} · "
            f"Kāraka {profile.get('primary_karaka')} · "
            f"Vāra {', '.join(profile.get('favorable_vara') or []) or '—'}"
        )
    candidates = result.get("candidates") or []
    rank_options = [int(item.get("rank") or 0) for item in candidates]
    if rank_options:
        current_rank = st.session_state.get("muhurta_selected_rank") or rank_options[0]
        if current_rank not in rank_options:
            current_rank = rank_options[0]
        selected = st.radio(
            t(language, "select_candidate"),
            rank_options,
            index=rank_options.index(current_rank),
            format_func=lambda rank: f"#{rank}",
            horizontal=True,
        )
        st.session_state.muhurta_selected_rank = selected
    for candidate in candidates:
        rank = candidate.get("rank")
        highlight = rank == st.session_state.get("muhurta_selected_rank")
        container = st.container(border=True)
        with container:
            zone = (result.get("location") or {}).get("timezone") or ""
            title = (
                f"#{rank}  "
                f"{format_local_window(candidate.get('start_time') or '', candidate.get('end_time') or '', zone)}"
            )
            if highlight:
                st.markdown(f"**{title}**")
            else:
                st.markdown(title)
            panch = candidate.get("panchanga") or {}
            hora = candidate.get("hora") or {}
            chart = candidate.get("chart") or {}
            karaka = candidate.get("karaka") or {}
            tara = candidate.get("tarabala") or {}
            cols = st.columns(5)
            cols[0].metric(t(language, "score"), f"{candidate.get('score')}%")
            cols[1].write(f"{t(language, 'status')}: {candidate.get('status')}")
            cols[2].write(f"{t(language, 'lagna')}: {chart.get('lagna_sign')}")
            cols[3].write(f"{t(language, 'chandra_lagna')}: {chart.get('chandra_lagna_sign')}")
            cols[4].write(f"{t(language, 'hora')}: {hora.get('lord')}")
            st.markdown(f"**{t(language, 'panchanga')}**")
            panch_cols = st.columns(5)
            panch_cols[0].write(f"{t(language, 'tithi')}: {tithi_label(panch)}")
            panch_cols[1].write(
                f"{t(language, 'vara')}: {panch.get('vara') or '—'} "
                f"({panch.get('vara_lord') or '—'})"
            )
            panch_cols[2].write(
                f"{t(language, 'nakshatra')}: {panch.get('nakshatra') or '—'} "
                f"{t(language, 'pada')} {panch.get('pada') or '—'}"
            )
            panch_cols[3].write(f"{t(language, 'karana')}: {panch.get('karana') or '—'}")
            panch_cols[4].write(f"{t(language, 'yoga')}: {panch.get('yoga') or '—'}")
            flags = panchanga_flags(panch)
            tara_line = (
                f"{t(language, 'tara')}: {tara.get('tara_name') or '—'} "
                f"({tara.get('tara_number') or '—'})"
            )
            karaka_line = f"{t(language, 'karaka')}: {karaka.get('primary_karaka') or '—'}"
            flag_line = (
                f"{t(language, 'flags')}: {', '.join(flags)}" if flags else ""
            )
            st.caption(" · ".join(part for part in (tara_line, karaka_line, flag_line) if part))
            strengths = candidate.get("strengths") or []
            if strengths:
                st.markdown("**" + t(language, "strengths") + "**")
                for item in strengths[:10]:
                    st.write("• " + (item.get("text") or ""))
            with st.expander(t(language, "view_data")):
                st.json(candidate)
            if candidate.get("hard_failures"):
                st.error(
                    t(language, "hard_failures")
                    + ": "
                    + "; ".join(item.get("text") for item in candidate["hard_failures"])
                )
            elif candidate.get("warnings"):
                st.warning(
                    t(language, "warnings")
                    + ": "
                    + "; ".join(item.get("text") for item in candidate["warnings"][:4])
                )

st.divider()
st.subheader(t(language, "step2"))
selected_rank = int(st.session_state.get("muhurta_selected_rank") or 1)
interpret_disabled = result is None or not gemini_ok or not (result.get("candidates") if result else None)
if st.button(t(language, "interpret"), disabled=interpret_disabled):
    with st.spinner("Gemini..."):
        explained = post_json(
            "/v1/muhurta/interpret",
            {
                "search_id": result.get("search_id") if result else None,
                "rank": selected_rank,
                "language": language,
                "calculated_result": result,
            },
            timeout=MUHURTA_TIMEOUT,
        )
        st.session_state.muhurta_interpretation = explained

interpretation = st.session_state.get("muhurta_interpretation")
if interpretation is None:
    st.caption(t(language, "no_gemini_yet"))
else:
    st.markdown(f"### {interpretation.get('title') or ''}")
    st.write(interpretation.get("summary") or "")
    st.markdown(f"**{t(language, 'why_best')}**")
    st.write(interpretation.get("why_this_is_best") or "")
    for item in interpretation.get("key_strengths") or []:
        st.markdown(f"**{item.get('title')}**")
        st.write(item.get("explanation") or "")
    if interpretation.get("panchanga_interpretation"):
        st.markdown(f"**{t(language, 'panchanga_notes')}**")
        st.write(interpretation.get("panchanga_interpretation"))
    if interpretation.get("planetary_interpretation"):
        st.markdown(f"**{t(language, 'planetary_notes')}**")
        st.write(interpretation.get("planetary_interpretation"))
    if interpretation.get("natal_compatibility"):
        st.markdown(f"**{t(language, 'natal_notes')}**")
        st.write(interpretation.get("natal_compatibility"))
    st.markdown(f"**{t(language, 'cautions')}**")
    cautions = interpretation.get("cautions") or []
    st.write("; ".join(cautions) if cautions else t(language, "none"))
    st.markdown(f"**{t(language, 'recommendation')}**")
    st.write(interpretation.get("final_recommendation") or "")
    sources = interpretation.get("sources") or []
    if sources:
        with st.expander(t(language, "sources")):
            for src in sources:
                st.caption(f"{src.get('source_file') or ''} · {src.get('source_heading') or ''}")
