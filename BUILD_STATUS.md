# Estado del MVP

- Version: `0.4.0`
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
- Wheel: `dist/ai_act_validator-0.4.0-py3-none-any.whl`
- SHA-256 del wheel: `a2c48e1ee9e1d2aa5bb2b40ac1d5ec2b7b16e0b15d02221bacf77cfe517042eb`

Integracion Power Platform opcional, pendiente de permisos del tenant:

- Crear la solucion y tablas en Dataverse.
- Desplegar la API en Azure.
- Registrar aplicaciones Entra.
- Importar el Custom Connector.
- Construir y publicar la Canvas App y el flujo.
