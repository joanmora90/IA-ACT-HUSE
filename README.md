# AI Act Validator

MVP web de un validador corporativo del Reglamento de IA de la UE:

- Streamlit: interfaz adaptativa en el navegador.
- FastAPI: motor juridico determinista y versionado.
- SQLite: expedientes, respuestas y resultados del MVP.
- Docker: ejecucion reproducible en Windows, macOS y Linux.

La interfaz principal usa el arbol, las preguntas, las rutas y los resultados del
**EU AI Act Compliance Checker** oficial. La instantanea integrada contiene 37 nodos y
45 resultados, con version oficial de 20 de julio de 2026. El resultado es informativo y
no sustituye la revision juridica.

Fuente y licencia: consulta `EU_SOURCE_ATTRIBUTION.md`.

## Inicio rapido en Windows

Requisito: Docker Desktop abierto y en funcionamiento.

1. Descomprime el paquete.
2. Haz doble clic en `INICIAR_WINDOWS.bat`.
3. Abre `http://localhost:8501` si el navegador no se abre automaticamente.

Para detenerlo, pulsa `Ctrl+C` en la ventana o ejecuta `DETENER_WINDOWS.bat`.

## Ejecutar en local

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
uvicorn ai_act_validator.main:app --reload
```

En otra terminal:

```bash
API_BASE_URL=http://localhost:8000 streamlit run src/ai_act_validator/ui.py
```

Interfaz: `http://localhost:8501`.

Documentacion API: `http://localhost:8000/docs`.

Con Docker:

```bash
docker compose up --build
```

Este comando inicia tanto la API como la interfaz.

## Publicar en Streamlit Community Cloud

1. Conecta este repositorio desde Streamlit Community Cloud.
2. Selecciona la rama `main`.
3. Usa como archivo principal `src/ai_act_validator/ui.py`.
4. No es necesario configurar secretos para el MVP.

En Streamlit Cloud, la interfaz carga el motor juridico dentro del mismo proceso. Con Docker,
la interfaz utiliza la API FastAPI independiente.

## Pruebas

```bash
pytest
ruff check .
```

## Estructura

- `src/ai_act_validator/data`: preguntas, reglas, obligaciones y fuentes.
- `tests`: casos juridicos y pruebas de API.
- `dataverse`: modelo opcional para una futura migracion a Dataverse.
- `power-platform`: integracion opcional para una futura migracion a Power Apps.
- `infra`: despliegue en Azure Container Apps.
- `docs`: puesta en marcha y controles de produccion.

## API principal

- `GET /api/v1/official-checker/version`
- `GET /api/v1/official-checker/start`
- `POST /api/v1/official-checker/answer`
- `POST /api/v1/official-checker/result`

Los endpoints siguientes corresponden al motor ampliado anterior y se mantienen por
compatibilidad:

- `POST /api/v1/assessments`
- `POST /api/v1/assessments/{id}/answers`
- `POST /api/v1/assessments/{id}/evaluate`
- `GET /api/v1/assessments/{id}/report`
- `POST /api/v1/evaluate`
- `POST /api/v1/power-platform/next-question`
- `POST /api/v1/power-platform/evaluate`
- `POST /api/v1/power-platform/report`
- `GET /api/v1/rules/version`

En desarrollo, el motor carga el ruleset incluido en el paquete. En produccion se configura
`RULE_SOURCE=dataverse`; la API carga preguntas, reglas y obligaciones desde las tablas
juridicas de Dataverse.

## Fuentes oficiales

- [Texto consolidado del Reglamento](https://eur-lex.europa.eu/eli/reg/2024/1689/2026-07-27/eng)
- [Calendario de aplicacion](https://digital-strategy.ec.europa.eu/en/policies/regulatory-framework-ai)
- [Directrices sobre sistemas de alto riesgo](https://digital-strategy.ec.europa.eu/en/policies/guidelines-ai-high-risk-systems)
- [EU AI Act Compliance Checker](https://ai-act-service-desk.ec.europa.eu/en/eu-ai-act-compliance-checker)
