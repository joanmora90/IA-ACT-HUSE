# Estado del MVP

- Version: `0.2.0`
- Ruleset: `EU_AI_ACT_2026_07_27_V0_1`
- Interfaz Streamlit adaptativa con motor FastAPI integrado para Streamlit Cloud
- Persistencia local SQLite
- Inicio simplificado para Windows
- Ruff: sin errores
- Swagger 2.0 del Custom Connector: valido
- Semillas Dataverse: generadas desde el ruleset canonico
- Pruebas: 21 superadas
- Flujo Streamlit completo y autonomo: verificado
- Wheel: `dist/ai_act_validator-0.2.0-py3-none-any.whl`
- SHA-256 del wheel: `f83941d9e88e4d1ea46482ababe04c8418d6f70e86f662a9560f11c2edba8025`

Integracion Power Platform opcional, pendiente de permisos del tenant:

- Crear la solucion y tablas en Dataverse.
- Desplegar la API en Azure.
- Registrar aplicaciones Entra.
- Importar el Custom Connector.
- Construir y publicar la Canvas App y el flujo.
