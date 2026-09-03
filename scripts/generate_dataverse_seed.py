from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "src" / "ai_act_validator" / "data"
OUTPUT = ROOT / "dataverse" / "seed"


def compact(value) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def write_csv(name: str, fieldnames: list[str], rows: list[dict]) -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    with (OUTPUT / name).open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def questions() -> None:
    payload = json.loads((DATA / "questions.json").read_text(encoding="utf-8"))
    rows = []
    for index, question in enumerate(payload["questions"], start=1):
        config = {
            key: value
            for key, value in question.items()
            if key
            not in {
                "id",
                "section",
                "text",
                "answer_type",
                "help",
                "legal_reference",
            }
        }
        rows.append(
            {
                "aia_name": f"{question['id']} - {question['section']}",
                "aia_code": question["id"],
                "aia_rulesetversion": payload["ruleset"],
                "aia_section": question["section"],
                "aia_text": question["text"],
                "aia_help": question.get("help", ""),
                "aia_answertype": question["answer_type"],
                "aia_legalreference": question["legal_reference"],
                "aia_sortorder": index,
                "aia_active": "true",
                "aia_configjson": compact(config),
            }
        )
    write_csv("questions.csv", list(rows[0]), rows)


def rules() -> None:
    payload = json.loads((DATA / "rules.json").read_text(encoding="utf-8"))
    rows = []
    for rule in payload["rules"]:
        effective_dates = [
            effect.get("effective_from")
            for effect in rule["effects"]
            if effect.get("effective_from")
        ]
        rows.append(
            {
                "aia_name": rule["id"],
                "aia_code": rule["id"],
                "aia_rulesetversion": payload["ruleset"],
                "aia_priority": rule["priority"],
                "aia_conditionjson": compact(rule["when"]),
                "aia_effectsjson": compact(rule["effects"]),
                "aia_legalreference": rule["legal_reference"],
                "aia_effectivefrom": min(effective_dates) if effective_dates else "",
                "aia_effectiveuntil": "",
                "aia_active": "true",
            }
        )
    write_csv("rules.csv", list(rows[0]), rows)


def obligations() -> None:
    payload = json.loads((DATA / "obligations.json").read_text(encoding="utf-8"))
    rows = []
    for item in payload["obligations"]:
        rows.append(
            {
                "aia_name": item["code"],
                "aia_code": item["code"],
                "aia_rulesetversion": payload["ruleset"],
                "aia_title": item["title"],
                "aia_legalreference": item["legal_reference"],
                "aia_appliesto": ";".join(item["applies_to"]),
                "aia_effectivefrom": item.get("effective_from", ""),
                "aia_applicabilityjson": compact(
                    {
                        key: value
                        for key, value in item.items()
                        if key
                        not in {
                            "code",
                            "title",
                            "legal_reference",
                            "applies_to",
                            "effective_from",
                        }
                    }
                ),
                "aia_active": "true",
            }
        )
    write_csv("obligations.csv", list(rows[0]), rows)


def legal_sources() -> None:
    payload = json.loads((DATA / "legal_sources.json").read_text(encoding="utf-8"))
    rows = [
        {
            "aia_name": item["title"],
            "aia_code": item["id"],
            "aia_url": item["url"],
            "aia_validfrom": payload["valid_from"],
            "aia_rulesetversion": payload["ruleset"],
        }
        for item in payload["sources"]
    ]
    write_csv("legal_sources.csv", list(rows[0]), rows)


if __name__ == "__main__":
    questions()
    rules()
    obligations()
    legal_sources()
    print(f"Semillas generadas en {OUTPUT}")
