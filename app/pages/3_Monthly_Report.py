from __future__ import annotations

import importlib
import json

import streamlit as st

import config as config_mod
import flatten as flatten_mod
import state as state_mod
import studio as studio_mod
import views as views_mod
from api_client import get_health, post_json
from flatten import retrieved_rule_count


def _bump_draft() -> None:
    st.session_state.studio_draft_rev = int(st.session_state.get("studio_draft_rev") or 0) + 1


def _seed_resend_widgets(draft: dict | None, rev: int) -> None:
    if not draft:
        return
    seeds = {
        f"draft_month_{rev}": draft.get("month") or "",
        f"draft_moon_{rev}": draft.get("moon_sign") or "",
        f"draft_email_subject_{rev}": draft.get("email_subject") or "",
        f"draft_email_preheader_{rev}": draft.get("email_preheader") or "",
        f"draft_email_body_{rev}": draft.get("email_body") or "",
    }
    for key, value in seeds.items():
        if key not in st.session_state:
            st.session_state[key] = value


def _marketing_configured() -> bool:
    checker = getattr(config_mod, "marketing_configured", None)
    if callable(checker):
        return bool(checker())
    url_fn = getattr(config_mod, "marketing_api_url", None)
    return bool(url_fn()) if callable(url_fn) else False


def _resend_payload(draft: dict | None) -> dict:
    payload_fn = getattr(studio_mod, "resend_email_payload", None)
    if callable(payload_fn) and draft is not None:
        return payload_fn(draft)
    draft = draft or {}
    return {
        "month": str(draft.get("month") or "").strip(),
        "moon_sign": str(draft.get("moon_sign") or "").strip(),
        "email_subject": str(draft.get("email_subject") or "").strip(),
        "email_preheader": str(draft.get("email_preheader") or "").strip(),
        "email_body": str(draft.get("email_body") or "").strip(),
        "language": "es",
    }


def _post_marketing_broadcast(payload: dict):
    import httpx

    url_fn = getattr(config_mod, "marketing_api_url", None)
    key_fn = getattr(config_mod, "marketing_api_key", None)
    base = url_fn() if callable(url_fn) else ""
    if not base:
        st.error("MARKETING_API_URL no está configurada.")
        return None
    url = f"{base}/v1/marketing/monthly-broadcasts"
    headers = {}
    token = key_fn() if callable(key_fn) else ""
    if token:
        headers["X-API-Key"] = token
    timeout = float(getattr(config_mod, "MARKETING_TIMEOUT", 60.0))
    try:
        response = httpx.post(url, json=payload, headers=headers, timeout=timeout)
    except httpx.HTTPError as exc:
        st.error(f"No se pudo conectar a Marketing Backend ({url}): {exc}")
        return None
    if response.status_code >= 400:
        st.error(f"{response.status_code} /v1/marketing/monthly-broadcasts: {response.text}")
        return None
    return response.json()


def _push_resend_draft(draft: dict | None):
    payload = _resend_payload(draft)
    try:
        import api_client as api_client_mod

        api_client_mod = importlib.reload(api_client_mod)
        sender = getattr(api_client_mod, "create_monthly_broadcast_draft", None)
        if callable(sender):
            return sender(payload)
    except Exception:
        pass
    return _post_marketing_broadcast(payload)


def _render_resend_draft_button(draft: dict | None) -> None:
    ready_fn = getattr(studio_mod, "can_push_resend_draft", None)
    ready = bool(ready_fn(draft)) if callable(ready_fn) else False
    configured = _marketing_configured()
    st.caption(
        "Crea un broadcast draft en Resend. No envía. "
        "Revisa y envía desde el dashboard de Resend."
    )
    if not configured:
        st.caption("Falta MARKETING_API_URL en StreamLit Package/.env.")
    elif not ready:
        st.caption("Necesitas signo lunar y cuerpo de email. Genera con Gemini primero.")
    if st.button(
        "Send draft to Resend",
        disabled=not ready or not configured,
        key="push_resend_draft",
    ):
        try:
            result = _push_resend_draft(draft)
        except Exception as exc:
            st.error(f"No se pudo crear el draft en Resend: {exc}")
            return
        if result:
            name = result.get("template_name") or result.get("name") or "Resend"
            subject = result.get("subject") or ""
            broadcast_id = result.get("resend_broadcast_id") or "—"
            st.success(f"Draft creado: {name} · {subject} · id {broadcast_id}")
            if result.get("review_hint"):
                st.caption(result["review_hint"])


config_mod = importlib.reload(config_mod)
flatten_mod = importlib.reload(flatten_mod)
state_mod = importlib.reload(state_mod)
studio_mod = importlib.reload(studio_mod)
views_mod = importlib.reload(views_mod)
render_report = views_mod.render_report
TRANSIT_TIMEOUT = config_mod.TRANSIT_TIMEOUT

st.set_page_config(page_title="Monthly Report Studio", layout="wide")
state_mod.init_state()

facts = st.session_state.get("facts")
rules = st.session_state.get("rules") or []
facts_id = studio_mod.facts_fingerprint(facts)
if st.session_state.get("studio_facts_id") != facts_id:
    st.session_state.studio_facts_id = facts_id
    st.session_state.studio_interval_include = None
    st.session_state.studio_rule_include = None
    st.session_state.studio_draft = (
        studio_mod.seed_draft(facts, rules, None) if facts else None
    )
    _bump_draft()

if st.session_state.studio_draft is None and facts:
    st.session_state.studio_draft = studio_mod.seed_draft(
        facts, rules, st.session_state.studio_interval_include
    )

rules_id = str(retrieved_rule_count(rules))
if facts and st.session_state.studio_draft is not None:
    if st.session_state.get("studio_rules_id") != rules_id:
        st.session_state.studio_rules_id = rules_id
        draft = st.session_state.studio_draft
        draft["chesta_bala_commentary"] = studio_mod.seed_chesta_commentary(facts, rules)
        st.session_state.studio_draft = draft
        _bump_draft()

interval_widget_key = f"studio_intervals_{facts_id}"
rule_widget_key = f"studio_rules_{facts_id}_{retrieved_rule_count(rules)}"
include_intervals = st.session_state.studio_interval_include
include_rules = st.session_state.studio_rule_include
ready = studio_mod.studio_readiness(facts, rules, include_intervals, include_rules)
health = get_health()
gemini_ok = bool(health and health.get("gemini_configured"))
rag_ok = bool(health and health.get("rag_configured"))

st.title("Monthly Report Studio")
st.caption(
    "Prepara el texto del informe. Gemini escribe desde los rangos de tránsito, "
    "las notas RAG de casa y las notas de Ceṣṭā Bala / Gati recuperadas."
)

metric_cols = st.columns(5)
metric_cols[0].metric("Month", ready["month"] or "—")
metric_cols[1].metric("Moon", ready["moon_sign"] or "—")
metric_cols[2].metric("Transit ranges", ready["selected_ranges"])
metric_cols[3].metric("RAG notes", ready["selected_rag"])
metric_cols[4].metric("Ceṣṭā Bala", "on")

if not facts:
    st.info("Calculate transits on Home first. The studio opens as soon as facts exist.")
    st.stop()

material_tab, draft_tab, preview_tab = st.tabs(["1. Material", "2. Draft", "3. Preview"])

with material_tab:
    st.markdown(
        "Selecciona qué verá Gemini. Los tres bloques están activos: "
        "rangos, RAG de casa y Ceṣṭā Bala."
    )
    range_col, rag_col, chesta_col = st.columns([1.2, 1.2, 0.8])

    with range_col:
        st.subheader("Transit ranges")
        st.caption("Intervalos calculados. Incluye o excluye rangos del brief.")
        interval_rows = studio_mod.interval_picker_rows(facts, rules, include_intervals)
        edited_intervals = st.data_editor(
            interval_rows,
            hide_index=True,
            width="stretch",
            disabled=[
                "Planet",
                "Period",
                "Sign",
                "House from Moon",
                "Gati",
                "Gati status",
                "Ceṣṭā Bala (virūpa)",
                "RAG meaning",
                "_key",
            ],
            column_order=[
                "Include",
                "Planet",
                "Period",
                "Sign",
                "House from Moon",
                "Gati",
                "Gati status",
                "Ceṣṭā Bala (virūpa)",
                "RAG meaning",
            ],
            column_config={"Include": st.column_config.CheckboxColumn(required=True)},
            key=interval_widget_key,
        )
        st.session_state.studio_interval_include = studio_mod.selection_from_editor(
            edited_intervals,
            st.session_state.studio_interval_include,
            kind="intervals",
            expected=len(interval_rows),
        )
        select_a, select_b = st.columns(2)
        if select_a.button("Include all ranges", key="include_all_ranges"):
            st.session_state.studio_interval_include = None
            st.session_state.pop(interval_widget_key, None)
            st.rerun()
        if select_b.button("Exclude all ranges", key="exclude_all_ranges"):
            st.session_state.studio_interval_include = []
            st.session_state.pop(interval_widget_key, None)
            st.rerun()

    with rag_col:
        st.subheader("RAG results")
        st.caption("Notas recuperadas. Solo las incluidas entran a Gemini.")
        if not rules:
            st.info("Retrieve interpretation rules on Home to load RAG notes here.")
        else:
            rule_rows = studio_mod.rule_picker_rows(rules, include_rules)
            edited_rules = st.data_editor(
                rule_rows,
                hide_index=True,
                width="stretch",
                disabled=[
                    "Planet",
                    "Sign",
                    "House from Moon",
                    "Gati",
                    "Source",
                    "RAG note",
                    "_key",
                ],
                column_order=[
                    "Include",
                    "Planet",
                    "Sign",
                    "House from Moon",
                    "Gati",
                    "Source",
                    "RAG note",
                ],
                column_config={"Include": st.column_config.CheckboxColumn(required=True)},
                key=rule_widget_key,
            )
            st.session_state.studio_rule_include = studio_mod.selection_from_editor(
                edited_rules,
                st.session_state.studio_rule_include,
                kind="rules",
                expected=len(rule_rows),
            )
            rag_a, rag_b = st.columns(2)
            if rag_a.button("Include all RAG", key="include_all_rag"):
                st.session_state.studio_rule_include = None
                st.session_state.pop(rule_widget_key, None)
                st.rerun()
            if rag_b.button("Exclude all RAG", key="exclude_all_rag"):
                st.session_state.studio_rule_include = []
                st.session_state.pop(rule_widget_key, None)
                st.rerun()

    with chesta_col:
        st.subheader("Ceṣṭā Bala")
        st.caption("Activo. Clasificación + notas RAG de Ceṣṭā Bala / Gati.")
        st.dataframe(studio_mod.chesta_rows(facts), width="stretch", hide_index=True)
        chesta_notes = studio_mod.chesta_note_rows(rules)
        if chesta_notes:
            st.dataframe(chesta_notes, width="stretch", hide_index=True)
        else:
            st.info("Retrieve interpretation rules to load Ceṣṭā Bala notes here.")

    include_intervals = st.session_state.studio_interval_include
    include_rules = st.session_state.studio_rule_include
    brief = studio_mod.gemini_brief(facts, rules, include_intervals, include_rules)
    st.divider()
    st.subheader("Gemini brief")
    st.caption("Este es el material que Gemini recibirá al generar.")
    st.download_button(
        "Download Gemini brief JSON",
        data=json.dumps(brief, ensure_ascii=False, indent=2),
        file_name="monthly-report-gemini-brief.json",
        mime="application/json",
        key="download_brief_json",
    )
    with st.expander("Inspect Gemini brief"):
        st.json(
            {
                "month": brief["month"],
                "moon_sign": brief["moon_sign"],
                "counts": brief["counts"],
                "chesta_bala": brief["chesta_bala"],
                "transit_ranges": brief["transit_ranges"],
                "retrieved_rule_planets": [
                    item.get("planet") for item in brief["retrieved_rules"]
                ],
            }
        )

with draft_tab:
    ready = studio_mod.studio_readiness(
        facts,
        rules,
        st.session_state.studio_interval_include,
        st.session_state.studio_rule_include,
    )
    draft = st.session_state.studio_draft or studio_mod.empty_draft(facts)
    action_a, action_b, action_c = st.columns(3)
    with action_a:
        if st.button("Seed draft from selected ranges", width="stretch"):
            st.session_state.studio_draft = studio_mod.seed_draft(
                facts, rules, st.session_state.studio_interval_include
            )
            _bump_draft()
            st.rerun()
    with action_b:
        generate_disabled = not ready["can_generate"] or not gemini_ok
        if st.button(
            "Generate with Gemini",
            type="primary",
            width="stretch",
            disabled=generate_disabled,
        ):
            payload = studio_mod.generate_request(
                facts,
                rules,
                st.session_state.studio_interval_include,
                st.session_state.studio_rule_include,
            )
            with st.spinner("Gemini is writing the Spanish monthly report..."):
                report = post_json("/v1/reports/monthly", payload, timeout=TRANSIT_TIMEOUT)
            if report is not None:
                st.session_state.report = report
                st.session_state.studio_draft = studio_mod.apply_gemini_report(draft, report)
                _bump_draft()
                st.rerun()
        if not gemini_ok:
            st.caption("Gemini is not configured on the API.")
        elif not rag_ok:
            st.caption("You can generate without RAG, but the language will be thinner.")
    with action_c:
        if st.button("Clear draft text", width="stretch"):
            st.session_state.studio_draft = studio_mod.empty_draft(facts)
            _bump_draft()
            st.rerun()

    draft = st.session_state.studio_draft or studio_mod.empty_draft(facts)
    rev = int(st.session_state.studio_draft_rev or 0)
    _seed_resend_widgets(draft, rev)
    draft["title"] = st.text_input(
        "Title", value=draft.get("title") or "", key=f"draft_title_{rev}"
    )
    meta_a, meta_b = st.columns(2)
    draft["month"] = meta_a.text_input("Month label", key=f"draft_month_{rev}")
    draft["moon_sign"] = meta_b.text_input("Moon sign", key=f"draft_moon_{rev}")
    draft["overview"] = st.text_area(
        "Overview",
        value=draft.get("overview") or "",
        height=160,
        key=f"draft_overview_{rev}",
    )

    st.markdown("### Major transits")
    updated_transits = []
    for index, item in enumerate(draft.get("major_transits") or []):
        planet = item.get("planet") or f"Transit {index + 1}"
        with st.expander(f"{planet} — {item.get('period') or ''}", expanded=True):
            item["period"] = st.text_input(
                "Period",
                value=item.get("period") or "",
                key=f"draft_period_{rev}_{index}",
            )
            item["title"] = st.text_input(
                "Title",
                value=item.get("title") or "",
                key=f"draft_item_title_{rev}_{index}",
            )
            item["interpretation"] = st.text_area(
                "Interpretation",
                value=item.get("interpretation") or "",
                height=180,
                key=f"draft_interp_{rev}_{index}",
            )
            notes = item.get("working_notes") or ""
            if notes:
                st.caption("Working notes from ranges + RAG")
                st.code(notes, language="markdown")
        updated_transits.append(item)
    draft["major_transits"] = updated_transits

    st.markdown("### Ceṣṭā Bala commentary")
    st.caption("Activo. Texto desde notas de Ceṣṭā Bala / Gati. Gemini lo reescribe al generar.")
    updated_chesta = []
    reserved = draft.get("chesta_bala_commentary") or []
    if not reserved:
        st.info("No classified Ceṣṭā Bala planets in the current facts.")
    for index, item in enumerate(reserved):
        item["commentary"] = st.text_area(
            f"{item.get('planet') or 'Planet'} — Ceṣṭā Bala",
            value=item.get("commentary") or "",
            height=160,
            key=f"draft_chesta_{rev}_{index}",
            placeholder="Se llena desde las notas de Ceṣṭā Bala recuperadas.",
        )
        updated_chesta.append(item)
    draft["chesta_bala_commentary"] = updated_chesta

    draft["recommendations"] = st.text_area(
        "Recommendations",
        value=draft.get("recommendations") or "",
        height=140,
        key=f"draft_recs_{rev}",
    )
    st.markdown("### Email")
    draft["email_subject"] = st.text_input("Email subject", key=f"draft_email_subject_{rev}")
    draft["email_preheader"] = st.text_input(
        "Email preheader", key=f"draft_email_preheader_{rev}"
    )
    draft["email_body"] = st.text_area(
        "Email body",
        height=420,
        key=f"draft_email_body_{rev}",
    )
    st.session_state.studio_draft = draft
    _render_resend_draft_button(draft)

with preview_tab:
    draft = st.session_state.studio_draft or studio_mod.empty_draft(facts)
    payload = studio_mod.report_payload(draft)
    render_report(payload)
    st.download_button(
        "Download report markdown",
        data=studio_mod.draft_markdown(draft),
        file_name="monthly-report-draft.md",
        mime="text/markdown",
        key="download_draft_md",
    )
    if st.session_state.report:
        with st.expander("Last Gemini JSON"):
            st.json(st.session_state.report)
