# Estado del MVP

- Version: `0.3.0`
- Ruleset principal: `EU_COMPLIANCE_CHECKER_2026_07_20`
- 37 nodos y 45 resultados oficiales de la Comision Europea
- Interfaz Streamlit adaptativa con motor oficial integrado
- Persistencia local SQLite
- Inicio simplificado para Windows
- Ruff: sin errores
- Swagger 2.0 del Custom Connector: valido
- Semillas Dataverse: generadas desde el ruleset canonico
- Pruebas: 27 superadas
- Flujo Streamlit completo y autonomo: verificado
- Wheel: `dist/ai_act_validator-0.3.0-py3-none-any.whl`
- SHA-256 del wheel: `47c27bc67d786f140073688ac5f6d1442557cdef8ecf3c64fd55e7eef9f9fc5a`

Integracion Power Platform opcional, pendiente de permisos del tenant:

- Crear la solucion y tablas en Dataverse.
- Desplegar la API en Azure.
- Registrar aplicaciones Entra.
- Importar el Custom Connector.
- Construir y publicar la Canvas App y el flujo.
