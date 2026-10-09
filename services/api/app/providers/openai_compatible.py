from __future__ import annotations

import json
from typing import Any

import httpx

from app.providers.base import ModelProvider, PlanModel, PlanStepModel
from app.providers.heuristic import HeuristicProvider, heuristic_plan
from app.security.injection import SYSTEM_RULES

last_error: str | None = None


def _remember_error(exc: Exception) -> None:
    global last_error
    text = str(exc)
    if "insufficient_quota" in text or "429" in text:
        last_error = "OpenAI quota exceeded. Appi is using the heuristic planner until billing is available."
    elif "401" in text or "invalid_api_key" in text:
        last_error = "OpenAI rejected the API key."
    else:
        last_error = "OpenAI request failed. Falling back to the heuristic planner where possible."


class OpenAICompatibleProvider(ModelProvider):
    name = "openai"

    def __init__(self, api_key: str, base_url: str = "https://api.openai.com/v1", model: str = "gpt-4o-mini") -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model or "gpt-4o-mini"
        if "api.openai.com" not in self.base_url:
            self.name = "openai_compatible"

    async def _chat(self, prompt: str, *, system: str | None = None, json_mode: bool = False) -> str:
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system or SYSTEM_RULES},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}
        async with httpx.AsyncClient(timeout=90) as client:
            response = await client.post(f"{self.base_url}/chat/completions", headers=headers, json=payload)
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                detail = exc.response.text[:300].replace(self.api_key, "[redacted]")
                raise RuntimeError(f"OpenAI request failed ({exc.response.status_code}): {detail}") from exc
            data = response.json()
        return data["choices"][0]["message"]["content"]

    async def generate(self, prompt: str, *, system: str | None = None) -> str:
        try:
            return await self._chat(prompt, system=system)
        except Exception as exc:
            _remember_error(exc)
            return await HeuristicProvider().generate(prompt, system=system)

    async def plan(self, goal: str, *, context: str = "") -> PlanModel:
        prompt = (
            "Create a JSON task plan with keys goal and steps. "
            "Each step needs id, description, tool, risk (low|medium|high), status=pending, "
            "depends_on, approval_required, and input object. "
            "Use the smallest sensible number of steps. Tools look like files.read_file or terminal.run_command.\n"
            f"Goal: {goal}\nContext:\n{context}"
        )
        try:
            raw = await self._chat(prompt, json_mode=True)
            start = raw.find("{")
            end = raw.rfind("}")
            parsed = json.loads(raw[start : end + 1])
            return PlanModel.model_validate(parsed)
        except Exception as exc:
            _remember_error(exc)
            return heuristic_plan(goal)

    async def classify_action(self, description: str) -> dict[str, Any]:
        try:
            raw = await self._chat(
                f'Classify risk as low, medium, high, or forbidden. JSON only {{"risk":"...","description":"..."}}: {description}',
                json_mode=True,
            )
            return json.loads(raw[raw.find("{") : raw.rfind("}") + 1])
        except Exception as exc:
            _remember_error(exc)
            return {"risk": "medium", "description": description}

    async def summarize(self, text: str) -> str:
        try:
            return await self._chat(f"Summarize for the user in 2-5 sentences:\n{text[:8000]}")
        except Exception as exc:
            _remember_error(exc)
            return await HeuristicProvider().summarize(text)

    async def tool_decision(self, goal: str, observation: str) -> dict[str, Any]:
        try:
            raw = await self._chat(
                f"Goal: {goal}\nObservation:\n{observation}\n"
                'Return JSON {"action":"continue|retry|replan|stop","reason":"..."}',
                json_mode=True,
            )
            return json.loads(raw[raw.find("{") : raw.rfind("}") + 1])
        except Exception as exc:
            _remember_error(exc)
            return {"action": "continue", "reason": observation[:400]}


class AnthropicProvider(ModelProvider):
    name = "anthropic"

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514") -> None:
        self.api_key = api_key
        self.model = model or "claude-sonnet-4-20250514"

    async def _chat(self, prompt: str, *, system: str | None = None) -> str:
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        payload = {
            "model": self.model,
            "max_tokens": 2000,
            "system": system or SYSTEM_RULES,
            "messages": [{"role": "user", "content": prompt}],
        }
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post("https://api.anthropic.com/v1/messages", headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
        return "".join(part.get("text", "") for part in data.get("content", []))

    async def generate(self, prompt: str, *, system: str | None = None) -> str:
        return await self._chat(prompt, system=system)

    async def plan(self, goal: str, *, context: str = "") -> PlanModel:
        try:
            raw = await self._chat(
                f"Return JSON plan with goal and steps for: {goal}\nContext:\n{context}"
            )
            parsed = json.loads(raw[raw.find("{") : raw.rfind("}") + 1])
            return PlanModel.model_validate(parsed)
        except Exception:
            return heuristic_plan(goal)

    async def classify_action(self, description: str) -> dict[str, Any]:
        return {"risk": "medium", "description": description}

    async def summarize(self, text: str) -> str:
        return await self._chat(f"Summarize:\n{text[:8000]}")

    async def tool_decision(self, goal: str, observation: str) -> dict[str, Any]:
        return {"action": "continue", "reason": observation[:400]}
