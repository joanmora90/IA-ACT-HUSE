from ai_act_validator.ui_helpers import enforceability_label, status_color, status_label


def test_status_label_is_translated():
    assert status_label("HIGH_RISK") == "Sistema de alto riesgo"


def test_unknown_status_has_readable_fallback():
    assert status_label("CUSTOM_STATUS") == "Custom Status"


def test_status_color_has_fallback():
    assert status_color("PROHIBITED") == "#b91c1c"
    assert status_color("UNKNOWN") == "#334155"


def test_enforceability_labels():
    assert enforceability_label(True) == "Actualmente exigible"
    assert enforceability_label(False) == "Aun no exigible"
    assert enforceability_label(None) == "Sin fecha determinada"
