"""A minimal, readable AI agent harness — built to teach harness engineering.

    from harness import Harness, AnthropicModel
    h = Harness(model=AnthropicModel(), workspace="./sandbox")
    result = h.run("Write a fizzbuzz in fizzbuzz.py and run it.")

Zero dependencies. See README.md and docs/ for the ideas behind it.
"""

from .agent import Harness, RunResult, DEFAULT_SYSTEM_PROMPT
from .context import ContextManager
from .guardrails import Guardrails, GuardrailViolation, Verdict
from .model import AnthropicModel, MockModel, ModelResponse, ToolCall
from .tools import Tool, ToolRegistry, build_default_tools
from .trace import Trace

__all__ = [
    "Harness", "RunResult", "DEFAULT_SYSTEM_PROMPT",
    "ContextManager", "Guardrails", "GuardrailViolation", "Verdict",
    "AnthropicModel", "MockModel", "ModelResponse", "ToolCall",
    "Tool", "ToolRegistry", "build_default_tools", "Trace",
]

__version__ = "0.1.0"
