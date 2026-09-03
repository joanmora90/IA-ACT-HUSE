# Formulas Power Fx

Los nombres visibles de tablas y columnas deben ajustarse a los que genere Dataverse.

## `App.OnStart`

```powerfx
Set(gblCurrentUser, User());
Set(gblRules, 'AI Act Validator API'.GetRulesVersion());
Clear(colAnswers)
```

## `btnStart.OnSelect`

```powerfx
Set(
    varProject,
    Patch(
        'Proyectos de IA',
        Defaults('Proyectos de IA'),
        {
            Nombre: txtProjectName.Value,
            Descripcion: txtDescription.Value,
            Departamento: txtDepartment.Value,
            'Responsable de negocio': gblCurrentUser.FullName,
            'Tipo de organizacion': cmbOrganisation.Selected,
            'Rol AI Act': cmbRole.Selected,
            'Puesta en produccion prevista': dpGoLive.SelectedDate,
            'Primera puesta en mercado': dpFirstMarket.SelectedDate
        }
    )
);
Set(
    varAssessment,
    Patch(
        'Evaluaciones AI Act',
        Defaults('Evaluaciones AI Act'),
        {
            Nombre: "EVA-" & Text(Now(), "yyyymmdd-hhmmss"),
            Proyecto: varProject,
            'Version del ruleset': gblRules.ruleset,
            Estado: 'Estado de evaluacion'.DRAFT,
            'Fecha de evaluacion': Today()
        }
    )
);
Clear(colAnswers);
Select(btnLoadNext)
```

## Cuerpo comun de las llamadas a la API

```powerfx
{
    project_name: varProject.Nombre,
    description: varProject.Descripcion,
    department: varProject.Departamento,
    owner: gblCurrentUser.FullName,
    organisation_type: cmbOrganisation.Selected.Code,
    role: cmbRole.Selected.Code,
    assessment_date: Text(Today(), "yyyy-mm-dd"),
    planned_go_live: Text(dpGoLive.SelectedDate, "yyyy-mm-dd"),
    first_placed_on_market: If(IsBlank(dpFirstMarket.SelectedDate), Blank(), Text(dpFirstMarket.SelectedDate, "yyyy-mm-dd")),
    answers: ShowColumns(colAnswers, question_id, value_json)
}
```

## `btnLoadNext.OnSelect`

```powerfx
Set(
    varNext,
    'AI Act Validator API'.GetNextQuestion(
        {
            project_name: varProject.Nombre,
            description: varProject.Descripcion,
            department: varProject.Departamento,
            owner: gblCurrentUser.FullName,
            organisation_type: cmbOrganisation.Selected.Code,
            role: cmbRole.Selected.Code,
            assessment_date: Text(Today(), "yyyy-mm-dd"),
            planned_go_live: Text(dpGoLive.SelectedDate, "yyyy-mm-dd"),
            first_placed_on_market: If(IsBlank(dpFirstMarket.SelectedDate), Blank(), Text(dpFirstMarket.SelectedDate, "yyyy-mm-dd")),
            answers: ShowColumns(colAnswers, question_id, value_json)
        }
    )
);
If(
    varNext.completed,
    Set(varResult, varNext.partial_result);
    Select(btnSaveResult),
    Set(varQuestion, varNext.next_question);
    Navigate(scrAssessment, ScreenTransition.Fade)
)
```

## Visibilidad de controles

```powerfx
// rdoBoolean.Visible
varQuestion.answer_type = "boolean"

// rdoSingle.Visible
varQuestion.answer_type = "choice" || varQuestion.answer_type = "dynamic_choice"

// galMulti.Visible
varQuestion.answer_type = "multi_choice"
```

## Opciones

```powerfx
// rdoBoolean.Items
Table(
    {code: "true", label: "Si"},
    {code: "false", label: "No"}
)

// rdoSingle.Items y galMulti.Items
varQuestion.options
```

Cada fila de `galMulti` incluye `chkOption`. Su valor se usa al construir el JSON.

## `btnAnswer.OnSelect`

```powerfx
Set(
    varValueJson,
    Switch(
        varQuestion.answer_type,
        "boolean",
            If(rdoBoolean.Selected.code = "true", "true", "false"),
        "choice",
            JSON(rdoSingle.Selected.code, JSONFormat.Compact),
        "dynamic_choice",
            JSON(rdoSingle.Selected.code, JSONFormat.Compact),
        "multi_choice",
            "[" &
            Concat(
                Filter(galMulti.AllItems, chkOption.Value),
                JSON(code, JSONFormat.Compact),
                ","
            ) &
            "]"
    )
);
Patch(
    'Respuestas AI Act',
    Coalesce(
        LookUp(
            'Respuestas AI Act',
            Evaluacion = varAssessment && 'Codigo de pregunta' = varQuestion.id
        ),
        Defaults('Respuestas AI Act')
    ),
    {
        Nombre: varAssessment.Nombre & "-" & varQuestion.id,
        Evaluacion: varAssessment,
        'Codigo de pregunta': varQuestion.id,
        'Valor JSON': varValueJson,
        'Respondida el': Now(),
        'Object ID del usuario': gblCurrentUser.Email
    }
);
RemoveIf(colAnswers, question_id = varQuestion.id);
Collect(colAnswers, {question_id: varQuestion.id, value_json: varValueJson});
Select(btnLoadNext)
```

## `btnSaveResult.OnSelect`

```powerfx
Patch(
    'Evaluaciones AI Act',
    varAssessment,
    {
        Estado: 'Estado de evaluacion'.COMPLETED,
        Ambito: varResult.scope,
        'Estado global': varResult.overall_status,
        Clasificacion: varResult.classification.status,
        'Base de clasificacion': varResult.classification.basis,
        'Evaluada el': Now(),
        'Respuestas JSON': JSON(colAnswers, JSONFormat.Compact),
        'Resultado JSON': JSON(varResult, JSONFormat.Compact)
    }
);
ForAll(
    varResult.obligations As item,
    Patch(
        'Obligaciones de evaluacion',
        Defaults('Obligaciones de evaluacion'),
        {
            Nombre: varAssessment.Nombre & "-" & item.code,
            Evaluacion: varAssessment,
            'Codigo de obligacion': item.code,
            Estado: "PENDIENTE"
        }
    )
);
ForAll(
    varResult.rules_triggered As item,
    Patch(
        'Trazas de regla',
        Defaults('Trazas de regla'),
        {
            Nombre: varAssessment.Nombre & "-" & item.rule_id,
            Evaluacion: varAssessment,
            'Codigo de regla': item.rule_id,
            Efecto: item.effect,
            'Base juridica': item.legal_reference,
            'Activada el': Now()
        }
    )
);
Navigate(scrResult, ScreenTransition.Fade)
```

## `btnReport.OnSelect`

```powerfx
Set(
    varReport,
    'AI Act Validator API'.GenerateReportHtml(
        {
            project_name: varProject.Nombre,
            description: varProject.Descripcion,
            department: varProject.Departamento,
            owner: gblCurrentUser.FullName,
            organisation_type: cmbOrganisation.Selected.Code,
            role: cmbRole.Selected.Code,
            assessment_date: Text(Today(), "yyyy-mm-dd"),
            planned_go_live: Text(dpGoLive.SelectedDate, "yyyy-mm-dd"),
            first_placed_on_market: If(IsBlank(dpFirstMarket.SelectedDate), Blank(), Text(dpFirstMarket.SelectedDate, "yyyy-mm-dd")),
            answers: ShowColumns(colAnswers, question_id, value_json)
        }
    )
);
PA_CreateAIActReport.Run(Text(varAssessment.'Evaluacion AI Act'), varAssessment.Nombre, varReport.html)
```
