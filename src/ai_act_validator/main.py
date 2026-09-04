from __future__ import annotations

import json
from pathlib import Path
from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.responses import HTMLResponse
from jinja2 import Environment, FileSystemLoader, select_autoescape

from .config import Settings, get_settings
from .dataverse_loader import load_rule_bundle
from .engine import LegalRulesEngine
from .models import (
    AnswerSubmission,
    AssessmentCreate,
    AssessmentResponse,
    AssessmentResult,
    EvaluateRequest,
    NextQuestionResponse,
    OfficialCheckerAnswerRequest,
    OfficialCheckerResultRequest,
    PowerPlatformRequest,
    ReportHtmlResponse,
)
from .official_checker import CheckerState, OfficialCheckerError, OfficialComplianceChecker
from .questions import QuestionCatalogue
from .repository import AssessmentNotFoundError, SQLiteAssessmentRepository
from .security import CurrentUser, EntraAuthenticator

TERMINAL_STATUSES = {
    "OUT_OF_SCOPE",
    "NOT_AI_SYSTEM",
    "EXCLUDED",
    "EXCLUDED_OPEN_SOURCE",
    "PROHIBITED",
}


def create_app(settings: Settings | None = None) -> FastAPI:
    effective_settings = settings or get_settings()
    rule_bundle = load_rule_bundle(effective_settings)
    questions = QuestionCatalogue(rule_bundle.questions)
    engine = LegalRulesEngine(
        rule_bundle.rules,
        rule_bundle.obligations,
        effective_settings.ruleset_id,
    )
    repository = SQLiteAssessmentRepository(effective_settings.database_path)
    official_checker = OfficialComplianceChecker()
    authenticator = EntraAuthenticator(effective_settings)
    templates = Environment(
        loader=FileSystemLoader(Path(__file__).parent / "templates"),
        autoescape=select_autoescape(["html"]),
    )

    api = FastAPI(
        title="AI Act Validator API",
        version="0.4.0",
        description=(
            "Motor juridico determinista para cribado inicial del Reglamento de IA de la UE."
        ),
    )
    api.state.settings = effective_settings
    api.state.questions = questions
    api.state.engine = engine
    api.state.repository = repository
    api.state.official_checker = official_checker

    def current_user(user: CurrentUser = Depends(authenticator.authenticate)) -> CurrentUser:
        return user

    def load_assessment(assessment_id: UUID):
        try:
            return repository.get(assessment_id)
        except AssessmentNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Evaluacion no encontrada") from exc

    def response_for(state, last_question_id: str | None = None) -> AssessmentResponse:
        state.result = engine.evaluate(
            state.metadata,
            state.answers,
            assessment_id=state.id,
        )
        terminal = state.result.overall_status in TERMINAL_STATUSES
        next_id = None if terminal else questions.next_unanswered(state.answers, last_question_id)
        repository.save(state)
        return AssessmentResponse(
            assessment=state,
            next_question=questions.view(next_id, state.answers) if next_id else None,
            completed=terminal or next_id is None,
        )

    def parse_power_platform_answers(request: PowerPlatformRequest) -> dict:
        answers = {}
        ordered_answers = sorted(request.answers, key=lambda item: int(item.question_id[1:]))
        for item in ordered_answers:
            try:
                value = json.loads(item.value_json)
                questions.validate_answer(
                    item.question_id, value, answers | {item.question_id: value}
                )
            except (json.JSONDecodeError, KeyError, ValueError) as exc:
                raise HTTPException(
                    status_code=422,
                    detail=f"Respuesta no valida en {item.question_id}: {exc}",
                ) from exc
            answers[item.question_id] = value
        return answers

    def next_question_response(metadata, answers, as_of_date=None) -> NextQuestionResponse:
        partial_result = engine.evaluate(metadata, answers, as_of=as_of_date)
        terminal = partial_result.overall_status in TERMINAL_STATUSES
        next_id = None if terminal else questions.next_unanswered(answers)
        return NextQuestionResponse(
            next_question=questions.view(next_id, answers) if next_id else None,
            completed=terminal or next_id is None,
            partial_result=partial_result,
        )

    @api.get("/health", tags=["system"])
    def health() -> dict[str, str]:
        return {"status": "ok", "ruleset": official_checker.ruleset}

    @api.get("/api/v1/official-checker/version", tags=["official-checker"])
    def official_checker_version(_: CurrentUser = Depends(current_user)) -> dict:
        return official_checker.source

    @api.get("/api/v1/official-checker/start", tags=["official-checker"])
    def official_checker_start(_: CurrentUser = Depends(current_user)) -> dict:
        state = official_checker.new_state()
        return {
            "state": state.snapshot(),
            "question": official_checker.question_view(state.current_question_id or ""),
        }

    @api.post("/api/v1/official-checker/answer", tags=["official-checker"])
    def official_checker_answer(
        request: OfficialCheckerAnswerRequest,
        _: CurrentUser = Depends(current_user),
    ) -> dict:
        state = CheckerState.from_snapshot(request.state)
        try:
            official_checker.submit(state, request.selected)
        except OfficialCheckerError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        return {
            "state": state.snapshot(),
            "question": (
                official_checker.question_view(state.current_question_id or "")
                if not state.completed
                else None
            ),
            "result": official_checker.result(state) if state.completed else None,
        }

    @api.post("/api/v1/official-checker/result", tags=["official-checker"])
    def official_checker_result(
        request: OfficialCheckerResultRequest,
        _: CurrentUser = Depends(current_user),
    ) -> dict:
        return official_checker.result(CheckerState.from_snapshot(request.state))

    @api.get("/api/v1/rules/version", tags=["rules"])
    def rules_version(_: CurrentUser = Depends(current_user)) -> dict[str, str]:
        source_payload = json.loads(
            (effective_settings.data_dir / "legal_sources.json").read_text(encoding="utf-8")
        )
        return {
            "ruleset": source_payload["ruleset"],
            "valid_from": source_payload["valid_from"],
            "assessment_baseline": source_payload["assessment_baseline"],
        }

    @api.post(
        "/api/v1/assessments",
        response_model=AssessmentResponse,
        status_code=status.HTTP_201_CREATED,
        tags=["assessments"],
        operation_id="StartAssessment",
    )
    def start_assessment(
        request: AssessmentCreate, _: CurrentUser = Depends(current_user)
    ) -> AssessmentResponse:
        state = repository.create(request.metadata)
        return response_for(state)

    @api.get(
        "/api/v1/assessments/{assessment_id}",
        response_model=AssessmentResponse,
        tags=["assessments"],
        operation_id="GetAssessment",
    )
    def get_assessment(
        assessment_id: UUID, _: CurrentUser = Depends(current_user)
    ) -> AssessmentResponse:
        return response_for(load_assessment(assessment_id))

    @api.post(
        "/api/v1/assessments/{assessment_id}/answers",
        response_model=AssessmentResponse,
        tags=["assessments"],
        operation_id="SubmitAnswer",
    )
    def submit_answer(
        assessment_id: UUID,
        submission: AnswerSubmission,
        _: CurrentUser = Depends(current_user),
    ) -> AssessmentResponse:
        state = load_assessment(assessment_id)
        expected_id = questions.next_unanswered(state.answers)
        replacing = submission.question_id in state.answers
        if not replacing and expected_id != submission.question_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"La siguiente pregunta esperada es {expected_id}",
            )
        try:
            questions.validate_answer(submission.question_id, submission.value, state.answers)
        except (KeyError, ValueError) as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

        if replacing:
            replaced_number = int(submission.question_id[1:])
            state.answers = {
                key: value
                for key, value in state.answers.items()
                if int(key[1:]) <= replaced_number
            }
        state.answers[submission.question_id] = submission.value
        return response_for(state, submission.question_id)

    @api.post(
        "/api/v1/assessments/{assessment_id}/evaluate",
        response_model=AssessmentResult,
        tags=["assessments"],
        operation_id="EvaluateAssessment",
    )
    def evaluate_assessment(
        assessment_id: UUID, _: CurrentUser = Depends(current_user)
    ) -> AssessmentResult:
        state = load_assessment(assessment_id)
        state.result = engine.evaluate(
            state.metadata,
            state.answers,
            assessment_id=state.id,
        )
        repository.save(state)
        return state.result

    @api.post(
        "/api/v1/evaluate",
        response_model=AssessmentResult,
        tags=["assessments"],
        operation_id="EvaluateStateless",
    )
    def evaluate_stateless(
        request: EvaluateRequest, _: CurrentUser = Depends(current_user)
    ) -> AssessmentResult:
        for question_id, value in request.answers.items():
            try:
                questions.validate_answer(question_id, value, request.answers)
            except (KeyError, ValueError) as exc:
                raise HTTPException(status_code=422, detail=str(exc)) from exc
        return engine.evaluate(
            request.metadata,
            request.answers,
            as_of=request.as_of_date,
        )

    @api.post(
        "/api/v1/power-platform/next-question",
        response_model=NextQuestionResponse,
        tags=["power-platform"],
        operation_id="GetNextQuestion",
    )
    def power_platform_next_question(
        request: PowerPlatformRequest, _: CurrentUser = Depends(current_user)
    ) -> NextQuestionResponse:
        answers = parse_power_platform_answers(request)
        return next_question_response(request.metadata(), answers, request.assessment_date)

    @api.post(
        "/api/v1/power-platform/evaluate",
        response_model=AssessmentResult,
        tags=["power-platform"],
        operation_id="EvaluateForPowerPlatform",
    )
    def power_platform_evaluate(
        request: PowerPlatformRequest, _: CurrentUser = Depends(current_user)
    ) -> AssessmentResult:
        answers = parse_power_platform_answers(request)
        return engine.evaluate(request.metadata(), answers, as_of=request.assessment_date)

    @api.post(
        "/api/v1/power-platform/report",
        response_model=ReportHtmlResponse,
        tags=["power-platform"],
        operation_id="GenerateReportHtml",
    )
    def power_platform_report(
        request: PowerPlatformRequest, _: CurrentUser = Depends(current_user)
    ) -> ReportHtmlResponse:
        answers = parse_power_platform_answers(request)
        metadata = request.metadata()
        result = engine.evaluate(metadata, answers, as_of=request.assessment_date)
        template = templates.get_template("assessment_report.html")
        assessment = {"metadata": metadata, "answers": answers}
        return ReportHtmlResponse(
            html=template.render(assessment=assessment, result=result, answers=answers)
        )

    @api.get(
        "/api/v1/assessments/{assessment_id}/report",
        response_class=HTMLResponse,
        tags=["assessments"],
        operation_id="GetAssessmentReport",
    )
    def assessment_report(
        assessment_id: UUID, _: CurrentUser = Depends(current_user)
    ) -> HTMLResponse:
        state = load_assessment(assessment_id)
        state.result = engine.evaluate(
            state.metadata,
            state.answers,
            assessment_id=state.id,
        )
        repository.save(state)
        template = templates.get_template("assessment_report.html")
        return HTMLResponse(
            template.render(assessment=state, result=state.result, answers=state.answers)
        )

    return api


app = create_app()
