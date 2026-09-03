from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "power-platform" / "custom-connector" / "apiDefinition.swagger.template.json"
OUTPUT = ROOT / "power-platform" / "custom-connector" / "apiDefinition.swagger.json"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", required=True, help="Host HTTPS sin protocolo ni ruta")
    parser.add_argument("--tenant-id", required=True)
    parser.add_argument("--api-client-id", required=True)
    args = parser.parse_args()

    content = TEMPLATE.read_text(encoding="utf-8")
    replacements = {
        "__API_HOST__": args.host,
        "__TENANT_ID__": args.tenant_id,
        "__API_CLIENT_ID__": args.api_client_id,
    }
    for old, new in replacements.items():
        content = content.replace(old, new)
    payload = json.loads(content)
    OUTPUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(OUTPUT)


if __name__ == "__main__":
    main()
