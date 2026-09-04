# Estado del MVP

- Version: `0.4.2`
- Ruleset principal: `EU_COMPLIANCE_CHECKER_2026_07_20`
- 37 nodos y 45 resultados oficiales de la Comision Europea
- Interfaz Streamlit adaptativa con motor oficial integrado
- Traduccion orientativa al espanol en preguntas y respuestas
- Enlaces directos a los articulos citados del AI Act y de EUR-Lex
- Persistencia local SQLite
- Inicio simplificado para Windows
- Ruff: sin errores
- Swagger 2.0 del Custom Connector: valido
- Semillas Dataverse: generadas desde el ruleset canonico
- Pruebas: 31 superadas
- Flujo Streamlit completo y autonomo: verificado
- Wheel: `dist/ai_act_validator-0.4.1-py3-none-any.whl`
- SHA-256 del wheel: `8fd59bed92845144a87a86863ffe0c890cc35cc8ac2de1133c8df0226eba03f7`

Integracion Power Platform opcional, pendiente de permisos del tenant:

- Crear la solucion y tablas en Dataverse.
- Desplegar la API en Azure.
- Registrar aplicaciones Entra.
- Importar el Custom Connector.
- Construir y publicar la Canvas App y el flujo.
