import csv
from pathlib import Path

from ai_act_validator.dataverse_loader import DataverseRulesLoader
from ai_act_validator.engine import LegalRulesEngine
from ai_act_validator.models import ProjectMetadata
from ai_act_validator.questions import QuestionCatalogue


def read_seed(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def test_dataverse_seed_reconstructs_the_ruleset(settings, monkeypatch):
    root = Path(__file__).resolve().parents[1]
    seed = root / "dataverse" / "seed"
    rows = {
        settings.dataverse_questions_entity_set: read_seed(seed / "questions.csv"),
        settings.dataverse_rules_entity_set: read_seed(seed / "rules.csv"),
        settings.dataverse_obligations_entity_set: read_seed(seed / "obligations.csv"),
    }
    for row in rows[settings.dataverse_questions_entity_set]:
        row["aia_sortorder"] = int(row["aia_sortorder"])
    for row in rows[settings.dataverse_rules_entity_set]:
        row["aia_priority"] = int(row["aia_priority"])

    loader = DataverseRulesLoader.__new__(DataverseRulesLoader)
    loader.settings = settings
    monkeypatch.setattr(loader, "_rows", lambda entity_set, select: rows[entity_set])
    bundle = loader.load()

    catalogue = QuestionCatalogue(bundle.questions)
    engine = LegalRulesEngine(bundle.rules, bundle.obligations, settings.ruleset_id)
    assert catalogue.first_id == "Q001"
    result = engine.evaluate(ProjectMetadata(project_name="Test"), {"Q001": False})
    assert result.overall_status == "OUT_OF_SCOPE"
