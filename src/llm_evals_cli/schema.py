from enum import Enum

from pydantic import BaseModel, Field, model_validator


class MetricEnum(str, Enum):
    exact_match = "exact_match"
    contains = "contains"
    regex = "regex"
    llm_judge = "llm_judge"


class Case(BaseModel):
    id: str | None = None
    prompt: str
    expected: str
    metric: MetricEnum
    system: str | None = None
    tags: list[str] = Field(default_factory=list)


class Suite(BaseModel):
    name: str
    description: str | None = None
    model: str = "gpt-4o-mini"
    base_url: str | None = None
    temperature: float = Field(0.0, ge=0.0, le=2.0)
    max_tokens: int = Field(1024, gt=0)
    cases: list[Case] = Field(min_length=1)

    @model_validator(mode="after")
    def assign_case_ids(self) -> "Suite":
        for i, case in enumerate(self.cases):
            if case.id is None:
                case.id = str(i + 1)
        return self
