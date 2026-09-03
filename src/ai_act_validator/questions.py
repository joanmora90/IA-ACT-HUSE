from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .conditions import matches
from .models import AnswerValue, QuestionOption, QuestionView


class QuestionCatalogue:
    def __init__(self, source: Path | dict[str, Any]):
        payload = (
            json.loads(source.read_text(encoding="utf-8")) if isinstance(source, Path) else source
        )
        self.ruleset = payload["ruleset"]
        self._questions = {item["id"]: item for item in payload["questions"]}
        self._order = [item["id"] for item in payload["questions"]]

    @property
    def first_id(self) -> str:
        return self._order[0]

    def raw(self, question_id: str) -> dict[str, Any]:
        try:
            return self._questions[question_id]
        except KeyError as exc:
            raise KeyError(f"Pregunta desconocida: {question_id}") from exc

    def view(self, question_id: str, answers: dict[str, AnswerValue]) -> QuestionView:
        item = self.raw(question_id)
        options = item.get("options", [])
        if item["answer_type"] == "dynamic_choice":
            source_value = answers.get(item["option_source"])
            options = item.get("option_groups", {}).get(str(source_value), [])
        return QuestionView(
            id=item["id"],
            section=item["section"],
            text=item["text"],
            answer_type=item["answer_type"],
            help=item.get("help", ""),
            legal_reference=item["legal_reference"],
            options=[QuestionOption.model_validate(option) for option in options],
            required=item.get("required", True),
        )

    def validate_answer(
        self, question_id: str, value: AnswerValue, answers: dict[str, AnswerValue]
    ) -> None:
        question = self.view(question_id, answers)
        answer_type = question.answer_type
        if answer_type == "boolean" and not isinstance(value, bool):
            raise ValueError("La respuesta debe ser true o false")
        if answer_type in {"choice", "dynamic_choice"}:
            if not isinstance(value, str):
                raise ValueError("La respuesta debe ser un codigo de opcion")
            allowed = {option.code for option in question.options}
            if value not in allowed:
                raise ValueError(f"Opcion no valida para {question_id}: {value}")
        if answer_type == "multi_choice":
            if (
                not isinstance(value, list)
                or not value
                or not all(isinstance(v, str) for v in value)
            ):
                raise ValueError("La respuesta debe ser una lista no vacia de codigos")
            if len(value) != len(set(value)):
                raise ValueError("La respuesta contiene opciones duplicadas")
            allowed = {option.code for option in question.options}
            unknown = set(value) - allowed
            if unknown:
                raise ValueError(f"Opciones no validas para {question_id}: {sorted(unknown)}")
            if "NONE" in value and len(value) > 1:
                raise ValueError("NONE no se puede combinar con otras opciones")

    def target_after(self, question_id: str, answers: dict[str, AnswerValue]) -> str:
        item = self.raw(question_id)
        context = {"answers": answers}
        for transition in item.get("transitions", []):
            if matches(transition["when"], context):
                return transition["target"]
        return item.get("default_next", "FINAL")

    def next_unanswered(
        self, answers: dict[str, AnswerValue], last_question_id: str | None = None
    ) -> str | None:
        current = (
            self.first_id
            if last_question_id is None
            else self.target_after(last_question_id, answers)
        )
        visited: set[str] = set()
        while current != "FINAL":
            if current in visited:
                raise RuntimeError("Ciclo detectado en el arbol de preguntas")
            visited.add(current)
            if current not in answers:
                return current
            current = self.target_after(current, answers)
        return None

    def all_views(self) -> list[QuestionView]:
        return [self.view(question_id, {}) for question_id in self._order if question_id != "Q009"]
