# Canvas App `AI Act Validator`

Formato recomendado: tableta, responsive, tema corporativo azul.

## Pantallas

| Pantalla | Funcion | Controles principales |
|---|---|---|
| `scrProjects` | Lista y alta de proyectos | `galProjects`, `btnNewProject` |
| `scrProject` | Metadatos del proyecto | `frmProject`, `cmbRole`, `cmbOrganisation`, `btnStart` |
| `scrAssessment` | Pregunta adaptativa | `lblSection`, `lblQuestion`, `lblHelp`, `rdoSingle`, `galMulti`, `btnAnswer` |
| `scrResult` | Clasificacion y obligaciones | `lblStatus`, `galObligations`, `galTrace`, `btnReport` |
| `scrReview` | Revision por validador | `frmReview`, `btnValidate` |

## Datos

- `aia_project`
- `aia_assessment`
- `aia_answer`
- `aia_assessmentobligation`
- `aia_ruletrace`
- Custom Connector `AI Act Validator API`

## Flujo de usuario

1. Crear proyecto y evaluacion en Dataverse.
2. Obtener la siguiente pregunta de la API.
3. Guardar cada respuesta en `aia_answer` como JSON.
4. Volver a llamar a `GetNextQuestion` con todas las respuestas.
5. Al finalizar, llamar a `EvaluateAssessment`.
6. Guardar resultado, obligaciones y trazas en Dataverse.
7. Generar informe y enviarlo a revision.

## Reglas de interfaz

- Nunca calcular la clasificacion con Power Fx.
- Mostrar siempre `legal_reference` y `help`.
- Bloquear el boton de continuar hasta que exista una respuesta valida.
- Mostrar por separado clasificacion, fecha de aplicacion y exigibilidad actual.
- Permitir cambiar una respuesta; al hacerlo, eliminar respuestas posteriores y reevaluar.

