# Dataverse

1. Crear una solucion no administrada `AIACTValidator` con prefijo `aia`.
2. Crear las tablas y roles descritos en `model.yaml`.
3. Importar, en este orden, `legal_sources.csv`, `questions.csv`, `rules.csv` y
   `obligations.csv`.
4. Activar auditoria en `aia_project`, `aia_assessment`, `aia_answer`,
   `aia_assessmentobligation` y `aia_ruletrace`.
5. Restringir escritura de tablas juridicas al rol `AI Act - Administrador juridico`.
6. Crear un usuario de aplicacion para la API con lectura de preguntas, reglas y
   obligaciones, sin permiso de escritura.

Los CSV se regeneran desde el ruleset canonico con:

```bash
python scripts/generate_dataverse_seed.py
```

En produccion, Dataverse es el sistema de registro y la fuente del ruleset. La API carga
preguntas, reglas y obligaciones desde estas tablas. Power Apps envia al endpoint
`/api/v1/power-platform/evaluate` las respuestas guardadas y almacena el resultado y la
traza devueltos.
