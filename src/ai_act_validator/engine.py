from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any
from uuid import UUID

from .conditions import get_path, matches
from .models import (
    AnswerValue,
    AssessmentResult,
    Classification,
    Finding,
    Obligation,
    ProjectMetadata,
    RuleTrace,
)


class LegalRulesEngine:
    def __init__(
        self,
        rules_source: Path | dict[str, Any],
        obligations_source: Path | dict[str, Any],
        ruleset: str,
    ):
        rules_payload = (
            json.loads(rules_source.read_text(encoding="utf-8"))
            if isinstance(rules_source, Path)
            else rules_source
        )
        obligations_payload = (
            json.loads(obligations_source.read_text(encoding="utf-8"))
            if isinstance(obligations_source, Path)
            else obligations_source
        )
        if rules_payload["ruleset"] != ruleset or obligations_payload["ruleset"] != ruleset:
            raise ValueError("La version de datos juridicos no coincide con RULESET_ID")
        self.ruleset = ruleset
        self.rules = sorted(rules_payload["rules"], key=lambda item: item["priority"], reverse=True)
        self.obligation_definitions = obligations_payload["obligations"]

    @staticmethod
    def _date(value: str | None) -> date | None:
        return date.fromisoformat(value) if value else None

    @staticmethod
    def _enforceable(effective_from: date | None, as_of: date) -> bool | None:
        return None if effective_from is None else as_of >= effective_from

    @staticmethod
    def _resolved(context: dict[str, Any], effect: dict[str, Any], key: str) -> Any:
        source = effect.get(f"{key}_from")
        return get_path(context, source) if source else effect.get(key)

    def evaluate(
        self,
        metadata: ProjectMetadata,
        answers: dict[str, AnswerValue],
        as_of: date | None = None,
        assessment_id: UUID | None = None,
    ) -> AssessmentResult:
        effective_as_of = as_of or metadata.assessment_date
        metadata_dict = metadata.model_dump(mode="json")
        context: dict[str, Any] = {"answers": answers, "metadata": metadata_dict}

        scope = "IN_SCOPE"
        scope_locked = False
        classification: Classification | None = None
        prohibited: list[Finding] = []
        transparency: list[Finding] = []
        traces: list[RuleTrace] = []

        for rule in self.rules:
            if not matches(rule["when"], context):
                continue
            for effect in rule["effects"]:
                effect_type = effect["type"]
                applied = False
                if effect_type == "set_scope" and not scope_locked:
                    scope = effect["value"]
                    scope_locked = True
                    applied = True
                elif effect_type == "set_classification" and classification is None:
                    effective_from = self._date(effect.get("effective_from"))
                    classification = Classification(
                        status=effect["status"],
                        basis=effect.get("basis"),
                        area=self._resolved(context, effect, "area"),
                        use_case=self._resolved(context, effect, "use_case"),
                        effective_from=effective_from,
                        currently_enforceable=self._enforceable(effective_from, effective_as_of),
                    )
                    applied = True
                elif effect_type == "add_prohibited":
                    effective_from = self._date(effect.get("effective_from"))
                    prohibited.append(
                        Finding(
                            code=effect["code"],
                            title=effect["title"],
                            legal_reference=effect["legal_reference"],
                            effective_from=effective_from,
                            currently_enforceable=self._enforceable(
                                effective_from, effective_as_of
                            ),
                        )
                    )
                    applied = True
                elif effect_type == "add_transparency":
                    effective_from = self._date(effect.get("effective_from"))
                    transparency.append(
                        Finding(
                            code=effect["code"],
                            title=effect["title"],
                            legal_reference=effect["legal_reference"],
                            effective_from=effective_from,
                            currently_enforceable=self._enforceable(
                                effective_from, effective_as_of
                            ),
                        )
                    )
                    applied = True
                if applied:
                    traces.append(
                        RuleTrace(
                            rule_id=rule["id"],
                            legal_reference=rule["legal_reference"],
                            effect=effect_type,
                        )
                    )

        if classification is None:
            classification = Classification(status="NOT_HIGH_RISK", basis="NO_HIGH_RISK_TRIGGER")

        if scope != "IN_SCOPE":
            classification = Classification(status="NOT_APPLICABLE", basis=scope)
            prohibited = []
            transparency = []

        if scope != "IN_SCOPE":
            overall_status = scope
        elif prohibited:
            overall_status = "PROHIBITED"
        elif classification.status == "HIGH_RISK":
            overall_status = "HIGH_RISK"
        elif transparency:
            overall_status = "TRANSPARENCY_OBLIGATIONS"
        else:
            overall_status = "NOT_HIGH_RISK"

        result_context = {
            "answers": answers,
            "metadata": metadata_dict,
            "result": {
                "scope": scope,
                "classification": classification.model_dump(mode="json"),
                "transparency_codes": [finding.code for finding in transparency],
                "prohibited_codes": [finding.code for finding in prohibited],
            },
        }
        obligations = self._applicable_obligations(
            result_context,
            metadata.role.value,
            classification.effective_from,
            {item.code: item.effective_from for item in transparency},
            effective_as_of,
        )

        recommendations: list[str] = []
        if prohibited:
            recommendations.append("No implantar el caso de uso y remitirlo a validacion juridica.")
        elif classification.status == "HIGH_RISK":
            recommendations.append(
                "Abrir plan de cumplimiento y recopilar evidencias antes de la fecha aplicable."
            )
        elif classification.basis == "ARTICLE_6_3_EXCEPTION":
            recommendations.append("Documentar expresamente la excepcion del articulo 6.3.")
        if scope == "IN_SCOPE":
            recommendations.append(
                "Revisar RGPD, normativa sectorial y Derecho nacional aplicable."
            )

        return AssessmentResult(
            assessment_id=assessment_id,
            ruleset=self.ruleset,
            as_of_date=effective_as_of,
            scope=scope,
            overall_status=overall_status,
            classification=classification,
            prohibited_practices=prohibited,
            transparency=transparency,
            obligations=obligations,
            recommendations=recommendations,
            rules_triggered=traces,
        )

    def _applicable_obligations(
        self,
        context: dict[str, Any],
        actor_role: str,
        classification_date: date | None,
        finding_dates: dict[str, date | None],
        as_of: date,
    ) -> list[Obligation]:
        applicable: list[Obligation] = []
        for item in self.obligation_definitions:
            if actor_role not in item["applies_to"]:
                continue
            if not matches(item["when"], context):
                continue
            if item.get("effective_from_result"):
                effective_from = classification_date
            elif item.get("effective_from_finding"):
                effective_from = finding_dates.get(item["effective_from_finding"])
            else:
                effective_from = self._date(item.get("effective_from"))
            applicable.append(
                Obligation(
                    code=item["code"],
                    title=item["title"],
                    legal_reference=item["legal_reference"],
                    applies_to=item["applies_to"],
                    effective_from=effective_from,
                    currently_enforceable=self._enforceable(effective_from, as_of),
                )
            )
        return applicable
