from ai_act_validator.official_checker import OfficialComplianceChecker


def answer(checker, state, selected):
    return checker.submit(state, selected)


def test_official_snapshot_shape():
    checker = OfficialComplianceChecker()
    assert checker.ruleset == "EU_COMPLIANCE_CHECKER_2026_07_20"
    assert len(checker.questions) == 37
    assert len(checker.flags_logic) == 45
    assert checker.question_view("Q1")["text"] == (
        "Do you want to check an AI model or an AI system?"
    )


def test_all_official_routes_and_content_are_resolvable():
    checker = OfficialComplianceChecker()
    for question_id, question in checker.questions.items():
        if question["type"] != "hub":
            view = checker.question_view(question_id)
            assert view["options"]
            assert view["text"]
        for route in question.get("routing", []):
            target = route["go_to"]
            assert target == "END" or target in checker.questions
    assert set(checker.flags_logic) == set(checker.flags_content)


def test_non_ai_system_finishes_outside_scope():
    checker = OfficialComplianceChecker()
    state = checker.new_state()
    answer(checker, state, [1])
    assert state.current_question_id == "QAIS 1"
    answer(checker, state, [1])
    assert state.completed
    result = checker.result(state)
    assert result["levels"]["risk_level"]
    assert state.flags["flag_ai_system_outsidescope"] is True
    assert "does not fall within the scope" in result["levels"]["risk_level"][0]["text"]


def test_prohibited_ai_system_path():
    checker = OfficialComplianceChecker()
    state = checker.new_state()
    for selected in ([1], [0], [0], [0], [4], [0]):
        answer(checker, state, list(selected))
    assert state.completed
    assert state.flags["flag_obligations_prohibitedsystems_result_output"] is True
    assert checker.result(state)["levels"]["obligation"]


def test_gpai_without_systemic_risk_provider_open_source():
    checker = OfficialComplianceChecker()
    state = checker.new_state()
    for selected in ([0], [0], [2], [0], [0]):
        answer(checker, state, list(selected))
    assert state.completed
    result = checker.result(state)
    assert state.flags["flag_risklevel_output_gpai_without_systemic_risk"] is True
    assert result["levels"]["role"]
    assert result["levels"]["risk_level"]
