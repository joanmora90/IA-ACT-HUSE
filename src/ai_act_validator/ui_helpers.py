from __future__ import annotations

STATUS_LABELS = {
    "OUT_OF_SCOPE": "Fuera del ambito del AI Act",
    "NOT_AI_SYSTEM": "No es un sistema de IA",
    "EXCLUDED": "Excluido del ambito",
    "EXCLUDED_OPEN_SOURCE": "Exclusion de codigo abierto",
    "PROHIBITED": "Practica prohibida",
    "HIGH_RISK": "Sistema de alto riesgo",
    "TRANSPARENCY_OBLIGATIONS": "Obligaciones de transparencia",
    "NOT_HIGH_RISK": "Sistema no clasificado como alto riesgo",
}

STATUS_COLORS = {
    "OUT_OF_SCOPE": "#64748b",
    "NOT_AI_SYSTEM": "#64748b",
    "EXCLUDED": "#64748b",
    "EXCLUDED_OPEN_SOURCE": "#64748b",
    "PROHIBITED": "#b91c1c",
    "HIGH_RISK": "#c2410c",
    "TRANSPARENCY_OBLIGATIONS": "#a16207",
    "NOT_HIGH_RISK": "#15803d",
}

ORGANISATION_TYPES = {
    "Organismo publico": "PUBLIC_BODY",
    "Prestador de servicio publico": "PUBLIC_SERVICE",
    "Organizacion privada": "PRIVATE",
    "Otro": "OTHER",
}

ACTOR_ROLES = {
    "Responsable del despliegue": "DEPLOYER",
    "Proveedor": "PROVIDER",
    "Importador": "IMPORTER",
    "Distribuidor": "DISTRIBUTOR",
    "Otro": "OTHER",
}


def status_label(status: str) -> str:
    return STATUS_LABELS.get(status, status.replace("_", " ").title())


def status_color(status: str) -> str:
    return STATUS_COLORS.get(status, "#334155")


def enforceability_label(value: bool | None) -> str:
    if value is True:
        return "Actualmente exigible"
    if value is False:
        return "Aun no exigible"
    return "Sin fecha determinada"
