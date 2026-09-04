from __future__ import annotations

import json
import re
from datetime import date
from html import escape
from typing import Any

import streamlit as st

from ai_act_validator.official_checker import (
    CheckerState,
    OfficialCheckerError,
    OfficialComplianceChecker,
)

AI_ACT_ARTICLE_URL = "https://ai-act-service-desk.ec.europa.eu/en/ai-act/article-{article}"
DIRECTIVE_ARTICLE_URLS = {
    "2011/93": "https://eur-lex.europa.eu/eli/dir/2011/93/oj/eng#art_{article}",
    "2016/680": "https://eur-lex.europa.eu/eli/dir/2016/680/oj/eng#art_{article}",
}
ARTICLE_REFERENCE = re.compile(
    r"\b(?P<prefix>Articles?|Artículos?|Art\.)\s+"
    r"(?P<numbers>\d+(?:\s*(?:(?:,|and|or|y|o)\s*)\d+)*)",
    re.IGNORECASE,
)


def _article_url(article: str, following_text: str) -> str:
    for directive, template in DIRECTIVE_ARTICLE_URLS.items():
        if directive in following_text:
            return template.format(article=article)
    return AI_ACT_ARTICLE_URL.format(article=article)


def link_article_references(value: str) -> str:
    """Escape text and link every cited article to its authoritative source."""

    escaped = escape(value)

    def replace_reference(match: re.Match[str]) -> str:
        following = escaped[match.end() : match.end() + 240]
        prefix = match.group("prefix")
        numbers = match.group("numbers")

        def replace_number(number_match: re.Match[str]) -> str:
            article = number_match.group(0)
            url = _article_url(article, following)
            return f'<a href="{url}" target="_blank" rel="noopener noreferrer">{article}</a>'

        linked_numbers = re.sub(r"\d+", replace_number, numbers)
        return f"{prefix} {linked_numbers}"

    return ARTICLE_REFERENCE.sub(replace_reference, escaped)


def bilingual_html(original: str, translation: str, css_class: str) -> str:
    translated = link_article_references(translation)
    return (
        f'<div class="{css_class}">{link_article_references(original)}</div>'
        f'<div class="translation">({translated})</div>'
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
        st.caption("Texto oficial en inglés. Traducción propia orientativa en español.")
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
    option_numbers = list(range(1, len(question["options"]) + 1))
    option_ids = {number: question["options"][number - 1]["id"] for number in option_numbers}
    if question["type"] == "radio":
        selected = st.radio(
            "Respuesta",
            option_numbers,
            index=None,
            format_func=lambda number: f"Opción {number}",
        )
        return [] if selected is None else [option_ids[selected]]
    selected = st.multiselect(
        "Respuesta",
        option_numbers,
        placeholder="Selecciona una o varias opciones",
        format_func=lambda number: f"Opción {number}",
    )
    return [option_ids[number] for number in selected]


def render_answer_options(question: dict[str, Any]) -> None:
    for number, option in enumerate(question["options"], start=1):
        st.markdown(
            f"""
            <div class="answer-card">
              <span class="answer-number">{number}</span>
              <div class="answer-copy">
                <div>{link_article_references(option["label"])}</div>
                <div class="translation">({link_article_references(option["label_es"])})</div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_question() -> None:
    engine = checker()
    state = CheckerState.from_snapshot(st.session_state.checker_state)
    question = engine.question_view(state.current_question_id or "")
    render_header(st.session_state.project["project_name"])
    answered = len(state.answers)
    st.progress(min(answered / 25, 0.95), text=f"{answered} respuestas registradas")
    st.caption(f"Pregunta oficial: {question['id']}")
    st.markdown(
        bilingual_html(question["title"], question["title_es"], "question-title"),
        unsafe_allow_html=True,
    )
    st.markdown(
        bilingual_html(question["text"], question["text_es"], "question-text"),
        unsafe_allow_html=True,
    )
    if question["info"]:
        with st.expander("Información de la pregunta"):
            st.markdown(question["info"])
    if question["sources"]:
        with st.expander("Fuentes jurídicas"):
            st.markdown(question["sources"])

    render_answer_options(question)
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
          .question-title {font-size: 1.55rem; font-weight: 700; line-height: 1.3;
                           margin-top: .5rem;}
          .question-text {font-size: 1.22rem; font-weight: 600; line-height: 1.45;
                          margin-top: 1.15rem;}
          .translation {font-size: .82rem; line-height: 1.45; color: #64748b;
                        margin-top: .2rem;}
          .answer-card {display: flex; gap: .75rem; align-items: flex-start;
                        padding: .8rem .9rem; margin: .55rem 0; border: 1px solid #dbe4ee;
                        border-radius: 12px; background: #f8fafc;}
          .answer-number {display: inline-flex; align-items: center; justify-content: center;
                          min-width: 1.7rem; height: 1.7rem; border-radius: 999px;
                          background: #145da0; color: white; font-weight: 700; font-size: .82rem;}
          .answer-copy {line-height: 1.45; flex: 1;}
          .question-title a, .question-text a, .answer-card a {color: #145da0;
                                                               text-decoration: underline;}
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
