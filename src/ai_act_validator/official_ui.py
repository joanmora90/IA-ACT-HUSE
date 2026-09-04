from __future__ import annotations

import json
from datetime import date
from html import escape
from typing import Any

import streamlit as st

from ai_act_validator.official_checker import (
    CheckerState,
    OfficialCheckerError,
    OfficialComplianceChecker,
)


@st.cache_resource
def checker() -> OfficialComplianceChecker:
    return OfficialComplianceChecker()


def initialise_state() -> None:
    defaults: dict[str, Any] = {
        "project": None,
        "checker_state": checker().new_state().snapshot(),
        "checker_history": [],
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def reset() -> None:
    st.session_state.project = None
    st.session_state.checker_state = checker().new_state().snapshot()
    st.session_state.checker_history = []


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


def render_sidebar() -> None:
    source = checker().source
    with st.sidebar:
        st.markdown("## ⚖️ AI Act Validator")
        st.caption("Árbol oficial de la Comisión Europea")
        st.divider()
        st.markdown(f"**Versión oficial:** {source['official_last_update']}")
        st.markdown(f"**Nodos:** {source['question_nodes']}")
        st.markdown(f"**Resultados:** {source['result_flags']}")
        st.link_button("Ver fuente oficial", source["source_page"], width="stretch")
        if st.session_state.project is not None:
            if st.button("Nueva evaluación", width="stretch"):
                reset()
                st.rerun()
        st.divider()
        st.caption(
            "Uso informativo. El resultado no sustituye la revisión de un profesional jurídico."
        )


def render_start() -> None:
    render_header("Compliance Checker oficial del Reglamento de IA de la UE")
    st.info("El árbol, las preguntas y los resultados proceden del EU AI Act Compliance Checker.")
    with st.form("project_form"):
        project_name = st.text_input("Nombre del proyecto *", max_chars=200)
        description = st.text_area(
            "Descripción del sistema o modelo",
            placeholder="Qué hace, para quién y qué decisiones apoya...",
            max_chars=5000,
        )
        col1, col2 = st.columns(2)
        department = col1.text_input("Departamento", max_chars=200)
        owner = col2.text_input("Responsable", max_chars=200)
        assessment_date = st.date_input("Fecha de evaluación", value=date.today())
        submitted = st.form_submit_button(
            "Comenzar evaluación oficial", type="primary", width="stretch"
        )
    if submitted:
        if not project_name.strip():
            st.error("Escribe el nombre del proyecto.")
            return
        st.session_state.project = {
            "project_name": project_name.strip(),
            "description": description.strip(),
            "department": department.strip(),
            "owner": owner.strip(),
            "assessment_date": assessment_date.isoformat(),
        }
        st.session_state.checker_state = checker().new_state().snapshot()
        st.session_state.checker_history = []
        st.rerun()


def answer_widget(question: dict[str, Any]) -> list[int]:
    labels = {option["label"]: option["id"] for option in question["options"]}
    if question["type"] == "radio":
        selected = st.radio("Respuesta", list(labels), index=None)
        return [] if selected is None else [labels[selected]]
    selected = st.multiselect("Respuesta", list(labels), placeholder="Selecciona una o varias")
    return [labels[label] for label in selected]


def render_question() -> None:
    engine = checker()
    state = CheckerState.from_snapshot(st.session_state.checker_state)
    question = engine.question_view(state.current_question_id or "")
    render_header(st.session_state.project["project_name"])
    answered = len(state.answers)
    st.progress(min(answered / 25, 0.95), text=f"{answered} respuestas registradas")
    st.caption(f"Pregunta oficial: {question['id']}")
    st.subheader(question["title"])
    st.markdown(f"### {question['text']}")
    if question["info"]:
        with st.expander("Información de la pregunta"):
            st.markdown(question["info"])
    if question["sources"]:
        with st.expander("Fuentes jurídicas"):
            st.markdown(question["sources"])

    with st.form(f"answer_{question['id']}"):
        selected = answer_widget(question)
        submitted = st.form_submit_button("Guardar y continuar", type="primary", width="stretch")

    back_col, _ = st.columns([1, 3])
    if back_col.button(
        "Atrás",
        disabled=not st.session_state.checker_history,
        width="stretch",
    ):
        st.session_state.checker_state = st.session_state.checker_history.pop()
        st.rerun()

    if submitted:
        try:
            previous = state.snapshot()
            engine.submit(state, selected)
            st.session_state.checker_history.append(previous)
            st.session_state.checker_state = state.snapshot()
            st.rerun()
        except OfficialCheckerError as exc:
            st.error(str(exc))


def render_result_items(items: list[dict[str, Any]], empty: str) -> None:
    if not items:
        st.info(empty)
        return
    for item in items:
        with st.container(border=True):
            st.markdown(item["text"])
            st.caption(f"Regla de salida: {item['flag']}")


def render_result() -> None:
    engine = checker()
    state = CheckerState.from_snapshot(st.session_state.checker_state)
    result = engine.result(state)
    render_header(st.session_state.project["project_name"])
    st.success("Evaluación completada")
    role_tab, risk_tab, obligation_tab, trace_tab = st.tabs(
        ["Tu rol", "Nivel de riesgo", "Obligaciones", "Trazabilidad"]
    )
    with role_tab:
        render_result_items(result["levels"]["role"], "No se ha determinado un rol.")
    with risk_tab:
        render_result_items(
            result["levels"]["risk_level"], "No se ha generado una clasificación de riesgo."
        )
    with obligation_tab:
        render_result_items(result["levels"]["obligation"], "No se han identificado obligaciones.")
    with trace_tab:
        st.dataframe(
            [
                {
                    "Orden": index + 1,
                    "Pregunta": answer["question_id"],
                    "Respuestas": ", ".join(map(str, answer["selected"])),
                }
                for index, answer in enumerate(result["answers"])
            ],
            hide_index=True,
            width="stretch",
        )
        st.code(result["ruleset"], language=None)

    export = {"project": st.session_state.project, "assessment": result}
    st.download_button(
        "Descargar evaluación JSON",
        data=json.dumps(export, ensure_ascii=False, indent=2),
        file_name="evaluacion-ai-act-oficial.json",
        mime="application/json",
        type="primary",
        width="stretch",
    )
    st.warning(result["disclaimer"])
    st.caption(
        "EU AI Act Compliance Checker © Unión Europea, reutilizado bajo CC BY 4.0. "
        "Interfaz e integración modificadas."
    )


def run() -> None:
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
                 background: linear-gradient(120deg, #0f2747 0%, #145da0 100%);
                 margin-bottom: 1.5rem;}
          .hero h1 {font-size: 2rem; margin: 0 0 .35rem 0;}
          .hero p {margin: 0; opacity: .9;}
        </style>
        """,
        unsafe_allow_html=True,
    )
    initialise_state()
    render_sidebar()
    if st.session_state.project is None:
        render_start()
        return
    state = CheckerState.from_snapshot(st.session_state.checker_state)
    if state.completed:
        render_result()
    else:
        render_question()
