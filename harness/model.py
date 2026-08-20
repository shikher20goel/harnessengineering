"""Model adapters — the ONLY place the harness touches an LLM API.

The harness is deliberately model-agnostic. Everything else in this package
works against the tiny interface defined here, which makes the whole system
testable offline (see MockModel) and portable across providers.

Interface:
    model.complete(system, messages, tools) -> ModelResponse

`messages` uses a provider-neutral shape:
    {"role": "user" | "assistant", "content": <str or list of blocks>}
Tool results are user messages with a list of blocks:
    {"type": "tool_result", "tool_use_id": ..., "content": ..., "is_error": bool}
"""

from __future__ import annotations

import json
import os
import urllib.request
from dataclasses import dataclass, field


@dataclass
class ToolCall:
    """A single tool invocation requested by the model."""
    id: str
    name: str
    arguments: dict


@dataclass
class ModelResponse:
    """Provider-neutral model output."""
    text: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)
    stop_reason: str = "end_turn"      # "end_turn" | "tool_use" | "max_tokens"
    usage: dict = field(default_factory=dict)

    @property
    def wants_tools(self) -> bool:
        return len(self.tool_calls) > 0


class AnthropicModel:
    """Thin adapter for the Anthropic Messages API (zero dependencies).

    Requires the ANTHROPIC_API_KEY environment variable.
    """

    API_URL = "https://api.anthropic.com/v1/messages"

    def __init__(self, model: str = "claude-sonnet-4-5", max_tokens: int = 4096,
                 api_key: str | None = None):
        self.model = model
        self.max_tokens = max_tokens
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY is not set. Export it, or use MockModel for offline runs."
            )

    def complete(self, system: str, messages: list[dict],
                 tools: list[dict]) -> ModelResponse:
        payload = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "system": system,
            "messages": messages,
            "tools": tools,
        }
        req = urllib.request.Request(
            self.API_URL,
            data=json.dumps(payload).encode(),
            headers={
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
        )
        with urllib.request.urlopen(req, timeout=300) as resp:
            data = json.loads(resp.read())

        text_parts, tool_calls = [], []
        for block in data.get("content", []):
            if block["type"] == "text":
                text_parts.append(block["text"])
            elif block["type"] == "tool_use":
                tool_calls.append(ToolCall(id=block["id"], name=block["name"],
                                           arguments=block["input"]))
        return ModelResponse(
            text="\n".join(text_parts),
            tool_calls=tool_calls,
            stop_reason=data.get("stop_reason", "end_turn"),
            usage=data.get("usage", {}),
        )


class MockModel:
    """A scripted model for tests and offline demos.

    Feed it a list of ModelResponse objects; each call to complete() pops the
    next one. This is what lets the ENTIRE harness be exercised without an
    API key — a small example of the harness-engineering principle that the
    scaffolding should be testable independently of the model.
    """

    def __init__(self, script: list[ModelResponse]):
        self.script = list(script)
        self.calls: list[dict] = []   # recorded inputs, for assertions

    def complete(self, system: str, messages: list[dict],
                 tools: list[dict]) -> ModelResponse:
        self.calls.append({"system": system, "messages": messages, "tools": tools})
        if not self.script:
            return ModelResponse(text="(mock script exhausted)", stop_reason="end_turn")
        return self.script.pop(0)
