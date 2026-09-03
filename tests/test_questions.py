from ai_act_validator.questions import QuestionCatalogue


def test_dynamic_annex_options(settings):
    catalogue = QuestionCatalogue(settings.data_dir / "questions.json")
    question = catalogue.view("Q009", {"Q008": "EMPLOYMENT"})
    assert {option.code for option in question.options} == {
        "EMP_RECRUITMENT",
        "EMP_WORK_DECISIONS",
        "NONE",
    }


def test_navigation_skips_annex_when_none(settings):
    catalogue = QuestionCatalogue(settings.data_dir / "questions.json")
    answers = {"Q008": "NONE"}
    assert catalogue.target_after("Q008", answers) == "Q013"


def test_none_cannot_be_combined(settings):
    catalogue = QuestionCatalogue(settings.data_dir / "questions.json")
    try:
        catalogue.validate_answer("Q004", ["NONE", "P01_MANIPULATION"], {})
    except ValueError as exc:
        assert "no se puede combinar" in str(exc)
    else:
        raise AssertionError("Se esperaba ValueError")
