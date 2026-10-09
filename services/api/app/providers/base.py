from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, Field


class PlanStepModel(BaseModel):
    id: str
    description: str
    tool: str
    risk: str = "low"
    status: str = "pending"
    depends_on: list[str] = Field(default_factory=list)
    approval_required: bool = False
    input: dict[str, Any] = Field(default_factory=dict)


class PlanModel(BaseModel):
    goal: str
    steps: list[PlanStepModel]


class ModelProvider(ABC):
    name: str = "base"

    @abstractmethod
    async def generate(self, prompt: str, *, system: str | None = None) -> str: ...

    @abstractmethod
    async def plan(self, goal: str, *, context: str = "") -> PlanModel: ...

    @abstractmethod
    async def classify_action(self, description: str) -> dict[str, Any]: ...

    @abstractmethod
    async def summarize(self, text: str) -> str: ...

    @abstractmethod
    async def tool_decision(self, goal: str, observation: str) -> dict[str, Any]: ...
