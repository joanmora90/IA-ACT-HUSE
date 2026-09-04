from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


class OfficialCheckerError(ValueError):
    pass


@dataclass
class CheckerState:
    current_question_id: str | None = "Q1"
    flags: dict[str, Any] = field(default_factory=dict)
    answers: list[dict[str, Any]] = field(default_factory=list)
    completed: bool = False

    def snapshot(self) -> dict[str, Any]:
        return {
            "current_question_id": self.current_question_id,
            "flags": deepcopy(self.flags),
            "answers": deepcopy(self.answers),
            "completed": self.completed,
        }

    @classmethod
    def from_snapshot(cls, value: dict[str, Any]) -> CheckerState:
        return cls(
            current_question_id=value.get("current_question_id"),
            flags=deepcopy(value.get("flags", {})),
            answers=deepcopy(value.get("answers", [])),
            completed=bool(value.get("completed", False)),
        )


class OfficialComplianceChecker:
    """Deterministic interpreter of the European Commission checker data files."""

    def __init__(self, data_dir: Path | None = None):
        base = data_dir or Path(__file__).parent / "data" / "eu_checker"
        self.logic_payload = json.loads((base / "logic.json").read_text(encoding="utf-8"))
        self.content_payload = json.loads((base / "content_es.json").read_text(encoding="utf-8"))
        self.source = json.loads((base / "source.json").read_text(encoding="utf-8"))
        self.questions: dict[str, dict[str, Any]] = self.logic_payload["questions_logic"]
        self.flags_logic: dict[str, dict[str, Any]] = self.logic_payload["flags_logic"]
        self.content: dict[str, dict[str, Any]] = self.content_payload["questions_content"]
        self.flags_content: dict[str, str] = self.content_payload["flags_content"]

    @property
    def ruleset(self) -> str:
        return self.source["ruleset"]

    def new_state(self) -> CheckerState:
        return CheckerState()

    def question_view(self, question_id: str) -> dict[str, Any]:
        logic = self.questions.get(question_id)
        content = self.content.get(question_id)
        if logic is None or content is None or logic.get("type") == "hub":
            raise OfficialCheckerError(f"Pregunta oficial no encontrada: {question_id}")
        options = []
        for answer_id, answer_logic in logic.get("answers", {}).items():
            answer_content = content.get("answers", {}).get(answer_id, {})
            options.append(
                {
                    "id": int(answer_id),
                    "label": answer_content.get("label", answer_id),
                    "help": answer_content.get("help", ""),
                    "exclusive": bool(answer_logic.get("exclusive", False)),
                }
            )
        return {
            "id": question_id,
            "title": content.get("main_title", ""),
            "text": content.get("secondary_title", ""),
            "info": content.get("info", ""),
            "sources": content.get("sources", ""),
            "type": logic["type"],
            "options": options,
        }

    def submit(self, state: CheckerState, selected: list[int]) -> CheckerState:
        if state.completed or state.current_question_id is None:
            raise OfficialCheckerError("La evaluacion ya ha finalizado.")
        question_id = state.current_question_id
        question = self.questions.get(question_id)
        if question is None or question.get("type") == "hub":
            raise OfficialCheckerError(f"Estado de pregunta no valido: {question_id}")

        valid_ids = {int(key) for key in question.get("answers", {})}
        unique_selected = list(dict.fromkeys(selected))
        if not unique_selected or not set(unique_selected).issubset(valid_ids):
            raise OfficialCheckerError("Selecciona al menos una respuesta valida.")
        if question["type"] == "radio" and len(unique_selected) != 1:
            raise OfficialCheckerError("Esta pregunta admite una sola respuesta.")
        exclusive = {
            int(key) for key, value in question.get("answers", {}).items() if value.get("exclusive")
        }
        if exclusive.intersection(unique_selected) and len(unique_selected) > 1:
            raise OfficialCheckerError("La opcion exclusiva no puede combinarse con otras.")

        flags = deepcopy(state.flags)
        for answer_id in unique_selected:
            answer = question["answers"][str(answer_id)]
            self._apply_flag_actions(answer.get("set_flags", []), flags)

        target: str | None = None
        for route in question.get("routing", []):
            if self._conditions_match(route.get("conditions", []), unique_selected, flags):
                self._apply_flag_actions(route.get("set_flags", []), flags)
                target = route.get("go_to")
                break
        if target is None:
            raise OfficialCheckerError(f"No existe una ruta oficial aplicable desde {question_id}.")

        next_id = self._resolve_hubs(target, flags)
        state.flags = flags
        state.answers.append({"question_id": question_id, "selected": unique_selected})
        state.current_question_id = next_id
        state.completed = next_id is None
        return state

    def result(self, state: CheckerState) -> dict[str, Any]:
        levels: dict[str, list[dict[str, Any]]] = {
            "role": [],
            "risk_level": [],
            "obligation": [],
        }
        for flag_name, value in state.flags.items():
            key = f"{flag_name}_{value}" if isinstance(value, str) else flag_name
            if not (value is True or isinstance(value, str)):
                continue
            content = self.flags_content.get(key)
            logic = self.flags_logic.get(key)
            if not content or not logic:
                continue
            level = logic.get("structure_level")
            if level not in levels:
                continue
            levels[level].append(
                {
                    "flag": key,
                    "text": content,
                    "priority": int(logic.get("priority_weight", 0)),
                }
            )
        for items in levels.values():
            items.sort(key=lambda item: item["priority"], reverse=True)
        return {
            "ruleset": self.ruleset,
            "official_last_update": self.source["official_last_update"],
            "source_page": self.source["source_page"],
            "answers": deepcopy(state.answers),
            "flags": deepcopy(state.flags),
            "levels": levels,
            "completed": state.completed,
            "disclaimer": (
                "Resultado informativo; no constituye asesoramiento juridico ni una "
                "evaluacion de la Comision Europea."
            ),
        }

    def _resolve_hubs(self, target: str, flags: dict[str, Any]) -> str | None:
        visited: set[str] = set()
        while target != "END":
            if target in visited:
                raise OfficialCheckerError(f"Bucle detectado en el nodo oficial {target}.")
            visited.add(target)
            question = self.questions.get(target)
            if question is None:
                raise OfficialCheckerError(f"Destino oficial desconocido: {target}")
            if question.get("type") != "hub":
                return target
            next_target = None
            for route in question.get("routing", []):
                if self._conditions_match(route.get("conditions", []), [], flags):
                    self._apply_flag_actions(route.get("set_flags", []), flags)
                    next_target = route.get("go_to")
                    break
            if next_target is None:
                raise OfficialCheckerError(f"El hub oficial {target} no tiene una ruta aplicable.")
            target = next_target
        return None

    def _apply_flag_actions(self, actions: list[dict[str, Any]], flags: dict[str, Any]) -> None:
        for action in actions:
            condition = action.get("condition")
            if condition and not self._flag_conditions_match(condition, flags):
                continue
            flags[action["flag_name"]] = action["value"]

    def _flag_conditions_match(
        self, conditions: list[dict[str, Any]], flags: dict[str, Any]
    ) -> bool:
        return all(self._flag_equals(item["flag_equals"], flags) for item in conditions)

    def _conditions_match(
        self,
        conditions: list[dict[str, Any]],
        selected: list[int],
        flags: dict[str, Any],
    ) -> bool:
        for condition in conditions:
            if "answer_is" in condition and condition["answer_is"] not in selected:
                return False
            if "if_any_answer_in" in condition and not any(
                value in selected for value in condition["if_any_answer_in"]
            ):
                return False
            if "if_none_selected_in" in condition and any(
                value in selected for value in condition["if_none_selected_in"]
            ):
                return False
            if "is_this_exact_match_selected" in condition and sorted(selected) != sorted(
                condition["is_this_exact_match_selected"]
            ):
                return False
            if "flag_equals" in condition and not self._flag_equals(
                condition["flag_equals"], flags
            ):
                return False
        return True

    @staticmethod
    def _flag_equals(condition: dict[str, Any], flags: dict[str, Any]) -> bool:
        name = condition["flag_name"]
        expected = condition["value"]
        if name not in flags and expected is False:
            return True
        return flags.get(name) == expected
