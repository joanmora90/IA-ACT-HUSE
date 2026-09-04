from __future__ import annotations

from datetime import UTC, date, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

AnswerValue = bool | str | int | float | list[str] | dict[str, Any] | None


class ActorRole(StrEnum):
    PROVIDER = "PROVIDER"
    DEPLOYER = "DEPLOYER"
    IMPORTER = "IMPORTER"
    DISTRIBUTOR = "DISTRIBUTOR"
    OTHER = "OTHER"


class OrganisationType(StrEnum):
    PUBLIC_BODY = "PUBLIC_BODY"
    PUBLIC_SERVICE = "PUBLIC_SERVICE"
    PRIVATE = "PRIVATE"
    OTHER = "OTHER"


class ProjectMetadata(BaseModel):
    project_name: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=5000)
    department: str = Field(default="", max_length=200)
    owner: str = Field(default="", max_length=200)
    organisation_type: OrganisationType = OrganisationType.OTHER
    role: ActorRole = ActorRole.DEPLOYER
    assessment_date: date = Field(default_factory=date.today)
    planned_go_live: date | None = None
    first_placed_on_market: date | None = None


class AssessmentCreate(BaseModel):
    metadata: ProjectMetadata


class AnswerSubmission(BaseModel):
    question_id: str = Field(pattern=r"^Q\d{3}$")
    value: AnswerValue


class QuestionOption(BaseModel):
    code: str
    label: str


class QuestionView(BaseModel):
    id: str
    section: str
    text: str
    answer_type: str
    help: str = ""
    legal_reference: str
    options: list[QuestionOption] = Field(default_factory=list)
    required: bool = True


class Finding(BaseModel):
    code: str
    title: str
    legal_reference: str
    effective_from: date | None = None
    currently_enforceable: bool | None = None


class RuleTrace(BaseModel):
    rule_id: str
    legal_reference: str
    effect: str


class Classification(BaseModel):
    status: str
    basis: str | None = None
    area: str | None = None
    use_case: str | None = None
    effective_from: date | None = None
    currently_enforceable: bool | None = None


class Obligation(BaseModel):
    code: str
    title: str
    legal_reference: str
    applies_to: list[str]
    effective_from: date | None = None
    currently_enforceable: bool | None = None


class AssessmentResult(BaseModel):
    assessment_id: UUID | None = None
    ruleset: str
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    as_of_date: date
    scope: str
    overall_status: str
    classification: Classification
    prohibited_practices: list[Finding] = Field(default_factory=list)
    transparency: list[Finding] = Field(default_factory=list)
    obligations: list[Obligation] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    rules_triggered: list[RuleTrace] = Field(default_factory=list)
    disclaimer: str = (
        "Resultado de cribado inicial. No sustituye la validacion del servicio juridico "
        "ni el analisis de normativa sectorial, proteccion de datos o legislacion nacional."
    )


class AssessmentState(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    metadata: ProjectMetadata
    answers: dict[str, AnswerValue] = Field(default_factory=dict)
    result: AssessmentResult | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class AssessmentResponse(BaseModel):
    assessment: AssessmentState
    next_question: QuestionView | None = None
    completed: bool = False


class EvaluateRequest(BaseModel):
    metadata: ProjectMetadata
    answers: dict[str, AnswerValue]
    as_of_date: date | None = None


class NextQuestionResponse(BaseModel):
    next_question: QuestionView | None = None
    completed: bool
    partial_result: AssessmentResult


class PowerPlatformAnswer(BaseModel):
    question_id: str = Field(pattern=r"^Q\d{3}$")
    value_json: str


class PowerPlatformRequest(BaseModel):
    project_name: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=5000)
    department: str = Field(default="", max_length=200)
    owner: str = Field(default="", max_length=200)
    organisation_type: OrganisationType = OrganisationType.OTHER
    role: ActorRole = ActorRole.DEPLOYER
    assessment_date: date = Field(default_factory=date.today)
    planned_go_live: date | None = None
    first_placed_on_market: date | None = None
    answers: list[PowerPlatformAnswer] = Field(default_factory=list)

    def metadata(self) -> ProjectMetadata:
        return ProjectMetadata(
            project_name=self.project_name,
            description=self.description,
            department=self.department,
            owner=self.owner,
            organisation_type=self.organisation_type,
            role=self.role,
            assessment_date=self.assessment_date,
            planned_go_live=self.planned_go_live,
            first_placed_on_market=self.first_placed_on_market,
        )


class ReportHtmlResponse(BaseModel):
    html: str


class OfficialCheckerAnswerRequest(BaseModel):
    state: dict[str, Any]
    selected: list[int]


class OfficialCheckerResultRequest(BaseModel):
    state: dict[str, Any]
