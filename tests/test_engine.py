from datetime import date

from ai_act_validator.models import ActorRole, OrganisationType, ProjectMetadata


def metadata(
    role: ActorRole = ActorRole.DEPLOYER,
    organisation_type: OrganisationType = OrganisationType.PRIVATE,
) -> ProjectMetadata:
    return ProjectMetadata(
        project_name="Caso de prueba",
        role=role,
        organisation_type=organisation_type,
        assessment_date=date(2026, 9, 1),
    )


def common_answers() -> dict:
    return {
        "Q001": True,
        "Q002": True,
        "Q003": "NONE",
        "Q004": ["NONE"],
        "Q006": False,
    }


def test_out_of_scope(engine):
    result = engine.evaluate(metadata(), {"Q001": False})
    assert result.scope == "OUT_OF_SCOPE"
    assert result.overall_status == "OUT_OF_SCOPE"
    assert result.classification.status == "NOT_APPLICABLE"


def test_prohibited_emotion_recognition_at_work(engine):
    answers = common_answers() | {
        "Q004": ["P06_EMOTION_WORK_EDU"],
        "Q005": ["NONE"],
    }
    result = engine.evaluate(metadata(), answers)
    assert result.overall_status == "PROHIBITED"
    assert [item.code for item in result.prohibited_practices] == ["P06_EMOTION_WORK_EDU"]
    assert result.prohibited_practices[0].currently_enforceable is True


def test_medical_safety_exception_avoids_emotion_prohibition(engine):
    answers = common_answers() | {
        "Q004": ["P06_EMOTION_WORK_EDU"],
        "Q005": ["EX_P06_MEDICAL_SAFETY"],
        "Q008": "NONE",
        "Q013": "NONE",
        "Q014": ["NONE"],
        "Q015": ["NONE"],
    }
    result = engine.evaluate(metadata(), answers)
    assert result.prohibited_practices == []
    assert result.overall_status == "NOT_HIGH_RISK"


def test_employment_recruitment_is_high_risk_and_fria_for_public_body(engine):
    answers = common_answers() | {
        "Q008": "EMPLOYMENT",
        "Q009": "EMP_RECRUITMENT",
        "Q010": False,
        "Q011": True,
        "Q013": "DIRECT_NOT_OBVIOUS",
        "Q014": ["NONE"],
        "Q015": ["NONE"],
    }
    result = engine.evaluate(metadata(ActorRole.DEPLOYER, OrganisationType.PUBLIC_BODY), answers)
    assert result.classification.status == "HIGH_RISK"
    assert result.classification.basis == "ARTICLE_6_2_ANNEX_III"
    assert result.classification.currently_enforceable is False
    assert [item.code for item in result.transparency] == ["ART_50_1"]
    obligation_codes = {item.code for item in result.obligations}
    assert {
        "OBL_AI_LITERACY",
        "OBL_DEPLOYER_HIGH_RISK",
        "OBL_DEPLOYER_NOTIFY_PERSONS",
        "OBL_FRIA",
        "OBL_PUBLIC_REGISTER",
    }.issubset(obligation_codes)


def test_article_6_3_exception_for_provider(engine):
    answers = common_answers() | {
        "Q008": "EMPLOYMENT",
        "Q009": "EMP_RECRUITMENT",
        "Q010": False,
        "Q011": False,
        "Q012": "PREPARATORY_TASK",
        "Q013": "NONE",
        "Q014": ["NONE"],
        "Q015": ["NONE"],
    }
    result = engine.evaluate(metadata(ActorRole.PROVIDER), answers)
    assert result.classification.status == "NOT_HIGH_RISK"
    assert result.classification.basis == "ARTICLE_6_3_EXCEPTION"
    assert "OBL_ART_6_3_DOCUMENTATION" in {item.code for item in result.obligations}


def test_chatbot_has_transparency_but_is_not_high_risk(engine):
    answers = common_answers() | {
        "Q008": "NONE",
        "Q013": "DIRECT_NOT_OBVIOUS",
        "Q014": ["SYNTHETIC_TEXT"],
        "Q015": ["NONE"],
    }
    result = engine.evaluate(metadata(ActorRole.PROVIDER), answers)
    assert result.classification.status == "NOT_HIGH_RISK"
    assert result.overall_status == "TRANSPARENCY_OBLIGATIONS"
    assert {item.code for item in result.transparency} == {"ART_50_1", "ART_50_2"}


def test_preexisting_synthetic_system_has_transition_until_december_2026(engine):
    project = metadata(ActorRole.PROVIDER)
    project.first_placed_on_market = date(2026, 7, 1)
    answers = common_answers() | {
        "Q008": "NONE",
        "Q013": "NONE",
        "Q014": ["SYNTHETIC_TEXT"],
        "Q015": ["NONE"],
    }
    result = engine.evaluate(project, answers)
    finding = next(item for item in result.transparency if item.code == "ART_50_2")
    assert finding.effective_from == date(2026, 12, 2)
    assert finding.currently_enforceable is False
    obligation = next(item for item in result.obligations if item.code == "OBL_ART_50_2")
    assert obligation.effective_from == date(2026, 12, 2)


def test_annex_i_date(engine):
    answers = common_answers() | {
        "Q006": True,
        "Q007": True,
        "Q013": "NONE",
        "Q014": ["NONE"],
        "Q015": ["NONE"],
    }
    result = engine.evaluate(metadata(), answers)
    assert result.classification.basis == "ARTICLE_6_1_ANNEX_I"
    assert result.classification.effective_from == date(2028, 8, 2)
    assert result.classification.currently_enforceable is False


def test_new_intimate_content_prohibition_is_not_yet_enforceable_on_baseline(engine):
    answers = common_answers() | {"Q004": ["P09_INTIMATE_CONTENT"]}
    result = engine.evaluate(metadata(), answers)
    assert result.overall_status == "PROHIBITED"
    assert result.prohibited_practices[0].effective_from == date(2026, 12, 2)
    assert result.prohibited_practices[0].currently_enforceable is False
