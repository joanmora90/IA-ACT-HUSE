from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import httpx
from azure.identity import ClientSecretCredential

from .config import Settings


@dataclass(frozen=True)
class RuleBundle:
    questions: dict[str, Any]
    rules: dict[str, Any]
    obligations: dict[str, Any]


class DataverseRulesLoader:
    def __init__(self, settings: Settings):
        required = {
            "DATAVERSE_URL": settings.dataverse_url,
            "DATAVERSE_TENANT_ID": settings.dataverse_tenant_id,
            "DATAVERSE_CLIENT_ID": settings.dataverse_client_id,
            "DATAVERSE_CLIENT_SECRET": settings.dataverse_client_secret,
        }
        missing = [name for name, value in required.items() if not value]
        if missing:
            raise RuntimeError(f"Configuracion Dataverse incompleta: {', '.join(missing)}")
        self.settings = settings
        self.base_url = settings.dataverse_url.rstrip("/")
        self.credential = ClientSecretCredential(
            tenant_id=settings.dataverse_tenant_id,
            client_id=settings.dataverse_client_id,
            client_secret=settings.dataverse_client_secret,
        )

    def _rows(self, entity_set: str, select: list[str]) -> list[dict[str, Any]]:
        token = self.credential.get_token(f"{self.base_url}/.default").token
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "OData-MaxVersion": "4.0",
            "OData-Version": "4.0",
        }
        query = {
            "$select": ",".join(select),
            "$filter": (
                f"aia_rulesetversion eq '{self.settings.ruleset_id}' and aia_active eq true"
            ),
        }
        url = f"{self.base_url}/api/data/v9.2/{entity_set}"
        rows: list[dict[str, Any]] = []
        with httpx.Client(timeout=30) as client:
            while url:
                response = client.get(url, headers=headers, params=query if not rows else None)
                response.raise_for_status()
                payload = response.json()
                rows.extend(payload.get("value", []))
                url = payload.get("@odata.nextLink")
        return rows

    def load(self) -> RuleBundle:
        rules_rows = self._rows(
            self.settings.dataverse_rules_entity_set,
            [
                "aia_code",
                "aia_priority",
                "aia_conditionjson",
                "aia_effectsjson",
                "aia_legalreference",
            ],
        )
        question_rows = self._rows(
            self.settings.dataverse_questions_entity_set,
            [
                "aia_code",
                "aia_section",
                "aia_text",
                "aia_help",
                "aia_answertype",
                "aia_legalreference",
                "aia_sortorder",
                "aia_configjson",
            ],
        )
        obligation_rows = self._rows(
            self.settings.dataverse_obligations_entity_set,
            [
                "aia_code",
                "aia_title",
                "aia_legalreference",
                "aia_appliesto",
                "aia_effectivefrom",
                "aia_applicabilityjson",
            ],
        )
        if not rules_rows or not question_rows or not obligation_rows:
            raise RuntimeError("El ruleset no esta completo en Dataverse")

        rules = [
            {
                "id": row["aia_code"],
                "priority": row["aia_priority"],
                "when": json.loads(row["aia_conditionjson"]),
                "effects": json.loads(row["aia_effectsjson"]),
                "legal_reference": row["aia_legalreference"],
            }
            for row in rules_rows
        ]

        questions = []
        for row in sorted(question_rows, key=lambda item: item["aia_sortorder"]):
            config = json.loads(row["aia_configjson"])
            questions.append(
                {
                    "id": row["aia_code"],
                    "section": row["aia_section"],
                    "text": row["aia_text"],
                    "answer_type": row["aia_answertype"],
                    "help": row.get("aia_help") or "",
                    "legal_reference": row["aia_legalreference"],
                }
                | config
            )

        obligations = []
        for row in obligation_rows:
            config = json.loads(row["aia_applicabilityjson"])
            obligation = {
                "code": row["aia_code"],
                "title": row["aia_title"],
                "legal_reference": row["aia_legalreference"],
                "applies_to": row["aia_appliesto"].split(";"),
            }
            if row.get("aia_effectivefrom"):
                obligation["effective_from"] = row["aia_effectivefrom"][:10]
            obligations.append(obligation | config)

        return RuleBundle(
            questions={"ruleset": self.settings.ruleset_id, "questions": questions},
            rules={"ruleset": self.settings.ruleset_id, "rules": rules},
            obligations={"ruleset": self.settings.ruleset_id, "obligations": obligations},
        )


def load_rule_bundle(settings: Settings) -> RuleBundle:
    if settings.rule_source == "dataverse":
        return DataverseRulesLoader(settings).load()
    return RuleBundle(
        questions=json.loads((settings.data_dir / "questions.json").read_text(encoding="utf-8")),
        rules=json.loads((settings.data_dir / "rules.json").read_text(encoding="utf-8")),
        obligations=json.loads(
            (settings.data_dir / "obligations.json").read_text(encoding="utf-8")
        ),
    )
