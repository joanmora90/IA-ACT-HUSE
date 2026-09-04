from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from urllib.request import Request, urlopen

BASE_URL = "https://europa.eu/assets/wcloud/widgets/202506/211c3a80-559a-11f0-b4dd-7fbfa4c84d38/"
SOURCE_PAGE = "https://ai-act-service-desk.ec.europa.eu/en/eu-ai-act-compliance-checker"
COPYRIGHT_PAGE = "https://ai-act-service-desk.ec.europa.eu/en/copyright-notice"
TARGET = Path(__file__).resolve().parents[1] / "src" / "ai_act_validator" / "data" / "eu_checker"


def download(name: str) -> bytes:
    request = Request(BASE_URL + name, headers={"User-Agent": "AI-Act-Validator/0.3"})
    with urlopen(request, timeout=90) as response:
        return response.read()


def write_json(path: Path, payload: object) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    logic_bytes = download("logic.json")
    content_bytes = download("content_es.json")
    logic = json.loads(logic_bytes)
    content = json.loads(content_bytes)

    if len(logic.get("questions_logic", {})) != 37:
        raise RuntimeError("El numero de nodos oficiales ha cambiado; revisa la integracion.")
    if len(logic.get("flags_logic", {})) != 45:
        raise RuntimeError("El numero de resultados oficiales ha cambiado; revisa la integracion.")
    if set(content.get("flags_content", {})) != set(logic["flags_logic"]):
        raise RuntimeError("El contenido y la logica oficiales no coinciden.")

    TARGET.mkdir(parents=True, exist_ok=True)
    write_json(TARGET / "logic.json", logic)
    write_json(TARGET / "content_es.json", content)
    write_json(
        TARGET / "source.json",
        {
            "ruleset": f"EU_COMPLIANCE_CHECKER_{logic['last_update_date'].replace('-', '_')}",
            "official_last_update": logic["last_update_date"],
            "retrieved_at": datetime.now(UTC).isoformat(),
            "source_page": SOURCE_PAGE,
            "copyright_page": COPYRIGHT_PAGE,
            "license": "CC BY 4.0",
            "logic_url": BASE_URL + "logic.json",
            "content_url": BASE_URL + "content_es.json",
            "logic_sha256": hashlib.sha256(logic_bytes).hexdigest(),
            "content_sha256": hashlib.sha256(content_bytes).hexdigest(),
            "question_nodes": len(logic["questions_logic"]),
            "result_flags": len(logic["flags_logic"]),
            "notice": (
                "Contenido reutilizado de la Union Europea. La interfaz y la integracion "
                "son modificaciones propias y no representan una evaluacion de la Comision Europea."
            ),
        },
    )


if __name__ == "__main__":
    main()
