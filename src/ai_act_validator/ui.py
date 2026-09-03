from __future__ import annotations

import json
import os
from datetime import date
from html import escape
from typing import Any

import httpx
import streamlit as st
from fastapi.testclient import TestClient

from ai_act_validator.main import create_app
from ai_act_validator.ui_helpers import (
    ACTOR_ROLES,
    ORGANISATION_TYPES,
    enforceability_label,
    status_color,
    status_label,
)

API_BASE_URL = os.getenv("API_BASE_URL", "").rstrip("/")
PUBLIC_API_BASE_URL = os.getenv("PUBLIC_API_BASE_URL", "").rstrip("/")

st.set_page_config(
    page_title="AI Act Validator",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
      .block-container {max-width: 1120px; padding-top: 2rem; padding-bottom: 4rem;}
      [data-testid="stSidebar"] {background: #0f2747;}
      [data-testid="stSidebar"] * {color: #f8fafc;}
      [data-testid="stSidebar"] .stButton button {color: #0f2747; background: #fff;}
      .hero {padding: 1.35rem 1.5rem; border-radius: 18px; color: white;
             background: linear-gradient(120deg, #0f2747 0%, #145da0 100%); margin-bottom: 1.5rem;}
      .hero h1 {font-size: 2rem; margin: 0 0 .35rem 0;}
      .hero p {margin: 0; opacity: .9;}
      .question-card {border: 1px solid #dbe4ee; border-radius: 16px; padding: 1.4rem 1.5rem;
                      background: #fff; box-shadow: 0 5px 18px rgba(15,39,71,.06);}
      .section-tag {display: inline-block; color: #145da0; background: #e8f2fb;
                    border-radius: 99px; padding: .25rem .7rem; font-size: .78rem;
                    font-weight: 700; letter-spacing: .04em;}
      .status-card {border-left: 8px solid var(--status-color); background: #fff;
                    border-radius: 14px; padding: 1.2rem 1.4rem;
                    box-shadow: 0 4px 16px rgba(15,39,71,.08);}
      .status-card h2 {color: var(--status-color); margin: 0 0 .25rem 0;}
      .muted {color: #64748b;}
      .legal {font-size: .86rem; color: #475569; margin-top: .6rem;}
      .item-card {border: 1px solid #e2e8f0; border-radius: 12px;
                  padding: .9rem 1rem; margin: .55rem 0;}
    </style>
    """,
    unsafe_allow_html=True,
)


def initialise_state() -> None:
    defaults = {
        "assessment_id": None,
        "assessment": None,
        "next_question": None,
        "completed": False,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


@st.cache_resource
def embedded_api_client() -> TestClient:
    return TestClient(create_app())


def raw_api_request(
    method: str, path: str, payload: dict[str, Any] | None = None
) -> httpx.Response:
    try:
        if API_BASE_URL:
            with httpx.Client(timeout=20, trust_env=False) as client:
                response = client.request(method, f"{API_BASE_URL}{path}", json=payload)
        else:
            response = embedded_api_client().request(method, path, json=payload)
        response.raise_for_status()
        return response
    except httpx.HTTPStatusError as exc:
        try:
            detail = exc.response.json().get("detail", exc.response.text)
        except (ValueError, AttributeError):
            detail = exc.response.text
        raise RuntimeError(f"La API rechazo la solicitud: {detail}") from exc
    except httpx.HTTPError as exc:
        raise RuntimeError(
            "No se puede conectar con el motor juridico. Comprueba que Docker sigue iniciado."
        ) from exc


def api_request(method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    return raw_api_request(method, path, payload).json()


def apply_assessment_response(payload: dict[str, Any]) -> None:
    assessment = payload["assessment"]
    st.session_state.assessment_id = assessment["id"]
    st.session_state.assessment = assessment
    st.session_state.next_question = payload.get("next_question")
    st.session_state.completed = payload.get("completed", False)


def reset_assessment() -> None:
    for key in ("assessment_id", "assessment", "next_question", "completed"):
        st.session_state.pop(key, None)
    initialise_state()


def render_sidebar() -> None:
    with st.sidebar:
        st.markdown("## ⚖️ AI Act Validator")
        st.caption("Cribado juridico inicial · MVP v0.2")
        st.divider()
        if st.session_state.assessment_id:
            st.markdown("**Evaluacion activa**")
            st.code(st.session_state.assessment_id, language=None)
            if st.button("Nueva evaluacion", width="stretch"):
                reset_assessment()
                st.rerun()
        else:
            with st.expander("Reanudar evaluacion"):
                resume_id = st.text_input("Identificador", placeholder="UUID de la evaluacion")
                if st.button("Reanudar", width="stretch", disabled=not resume_id):
                    try:
                        apply_assessment_response(
                            api_request("GET", f"/api/v1/assessments/{resume_id.strip()}")
                        )
                        st.rerun()
                    except RuntimeError as exc:
                        st.error(str(exc))
        st.divider()
        st.caption("El resultado no sustituye la revision del servicio juridico.")


def render_header(subtitle: str) -> None:
    st.markdown(
        f"""
        <div class="hero">
          <h1>AI Act Validator</h1>
          <p>{escape(subtitle)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_start() -> None:
    render_header("Evaluacion inicial de conformidad con el Reglamento de IA de la UE")
    st.subheader("Datos del proyecto")
    with st.form("start_assessment"):
        project_name = st.text_input("Nombre del proyecto *", max_chars=200)
        description = st.text_area(
            "Descripcion del sistema",
            placeholder="Que hace, para quien y que decisiones apoya...",
            max_chars=5000,
        )
        col1, col2 = st.columns(2)
        with col1:
            department = st.text_input("Departamento", max_chars=200)
            organisation_label = st.selectbox("Tipo de organizacion", ORGANISATION_TYPES)
            assessment_date = st.date_input("Fecha de evaluacion", value=date.today())
        with col2:
            owner = st.text_input("Responsable", max_chars=200)
            role_label = st.selectbox("Rol respecto al sistema", ACTOR_ROLES)
            has_go_live = st.checkbox("Indicar fecha prevista de puesta en marcha")
            planned_go_live = (
                st.date_input("Puesta en marcha prevista", value=date.today())
                if has_go_live
                else None
            )

        submitted = st.form_submit_button("Comenzar evaluacion", type="primary", width="stretch")

    if submitted:
        if not project_name.strip():
            st.error("Escribe el nombre del proyecto.")
            return
        payload = {
            "metadata": {
                "project_name": project_name.strip(),
                "description": description.strip(),
                "department": department.strip(),
                "owner": owner.strip(),
                "organisation_type": ORGANISATION_TYPES[organisation_label],
                "role": ACTOR_ROLES[role_label],
                "assessment_date": assessment_date.isoformat(),
                "planned_go_live": planned_go_live.isoformat() if planned_go_live else None,
            }
        }
        try:
            apply_assessment_response(api_request("POST", "/api/v1/assessments", payload))
            st.rerun()
        except RuntimeError as exc:
            st.error(str(exc))


def answer_widget(question: dict[str, Any]) -> Any:
    answer_type = question["answer_type"]
    options = question.get("options", [])
    labels = {option["label"]: option["code"] for option in options}

    if answer_type == "boolean":
        selected = st.radio("Respuesta", ["Si", "No"], index=None, horizontal=True)
        return None if selected is None else selected == "Si"
    if answer_type in {"choice", "dynamic_choice"}:
        selected = st.selectbox(
            "Respuesta",
            list(labels),
            index=None,
            placeholder="Selecciona una opcion",
        )
        return labels.get(selected) if selected else None
    if answer_type == "multi_choice":
        selected = st.multiselect("Respuesta", list(labels), placeholder="Selecciona una o varias")
        return [labels[item] for item in selected]
    st.error(f"Tipo de pregunta no soportado: {answer_type}")
    return None


def render_question() -> None:
    question = st.session_state.next_question
    assessment = st.session_state.assessment
    answers = assessment.get("answers", {})
    render_header(assessment["metadata"]["project_name"])
    st.progress(min(len(answers) / 15, 0.95), text=f"{len(answers)} respuestas registradas")

    st.markdown(
        f"""
        <div class="question-card">
          <span class="section-tag">{escape(question["section"])}</span>
          <h2>{escape(question["id"])} · {escape(question["text"])}</h2>
          <p class="muted">{escape(question.get("help", ""))}</p>
          <p class="legal">Base juridica: {escape(question["legal_reference"])}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.write("")

    with st.form(f"answer_{question['id']}"):
        answer = answer_widget(question)
        submitted = st.form_submit_button("Guardar y continuar", type="primary", width="stretch")

    if submitted:
        if answer is None or answer == []:
            st.error("Selecciona una respuesta.")
            return
        if isinstance(answer, list) and "NONE" in answer and len(answer) > 1:
            st.error("La opcion 'Ninguna' no puede combinarse con otras opciones.")
            return
        try:
            apply_assessment_response(
                api_request(
                    "POST",
                    f"/api/v1/assessments/{st.session_state.assessment_id}/answers",
                    {"question_id": question["id"], "value": answer},
                )
            )
            st.rerun()
        except RuntimeError as exc:
            st.error(str(exc))


def render_items(items: list[dict[str, Any]], empty_message: str) -> None:
    if not items:
        st.info(empty_message)
        return
    for item in items:
        effective = item.get("effective_from") or "Sin fecha especifica"
        enforceable = enforceability_label(item.get("currently_enforceable"))
        st.markdown(
            f"""
            <div class="item-card">
              <strong>{escape(item.get("title", item.get("code", "")))}</strong><br>
              <span class="muted">{escape(item.get("legal_reference", ""))}</span><br>
              <small>{escape(enforceable)} · Aplicacion: {escape(str(effective))}</small>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_result() -> None:
    assessment = st.session_state.assessment
    result = assessment["result"]
    status = result["overall_status"]
    classification = result["classification"]
    render_header(assessment["metadata"]["project_name"])
    st.progress(1.0, text="Evaluacion completada")
    st.markdown(
        f"""
        <div class="status-card" style="--status-color:{status_color(status)}">
          <h2>{escape(status_label(status))}</h2>
          <span class="muted">Clasificacion: {escape(status_label(classification["status"]))}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.write("")

    col1, col2, col3 = st.columns(3)
    col1.metric("Ambito", result["scope"].replace("_", " "))
    col2.metric("Base", classification.get("basis") or "—")
    col3.metric("Fecha evaluada", result["as_of_date"])

    summary_tab, obligations_tab, trace_tab, report_tab = st.tabs(
        ["Resumen", "Obligaciones", "Trazabilidad", "Informe"]
    )
    with summary_tab:
        st.subheader("Practicas prohibidas")
        render_items(result.get("prohibited_practices", []), "No se han detectado.")
        st.subheader("Transparencia")
        render_items(result.get("transparency", []), "No se han detectado obligaciones.")
        st.subheader("Recomendaciones")
        for recommendation in result.get("recommendations", []):
            st.markdown(f"- {recommendation}")

    with obligations_tab:
        render_items(result.get("obligations", []), "No se han identificado obligaciones.")

    with trace_tab:
        traces = result.get("rules_triggered", [])
        if traces:
            st.dataframe(
                [
                    {
                        "Regla": item["rule_id"],
                        "Base juridica": item["legal_reference"],
                        "Efecto": item["effect"],
                    }
                    for item in traces
                ],
                width="stretch",
                hide_index=True,
            )
        else:
            st.info("No hay reglas activadas.")
        st.caption(f"Ruleset: {result['ruleset']}")

    with report_tab:
        st.write("Consulta el informe completo en una nueva pestaña o descarga el resultado JSON.")
        report_path = f"/api/v1/assessments/{st.session_state.assessment_id}/report"
        if PUBLIC_API_BASE_URL:
            st.link_button(
                "Abrir informe HTML",
                f"{PUBLIC_API_BASE_URL}{report_path}",
                type="primary",
                width="stretch",
            )
        else:
            try:
                report_html = raw_api_request("GET", report_path).text
                st.download_button(
                    "Descargar informe HTML",
                    data=report_html,
                    file_name=f"informe-{st.session_state.assessment_id}.html",
                    mime="text/html",
                    type="primary",
                    width="stretch",
                )
            except RuntimeError as exc:
                st.error(str(exc))
        st.download_button(
            "Descargar resultado JSON",
            data=json.dumps(result, ensure_ascii=False, indent=2),
            file_name=f"evaluacion-{st.session_state.assessment_id}.json",
            mime="application/json",
            width="stretch",
        )


initialise_state()
render_sidebar()

if st.session_state.assessment_id is None:
    render_start()
elif st.session_state.completed or st.session_state.next_question is None:
    render_result()
else:
    render_question()
