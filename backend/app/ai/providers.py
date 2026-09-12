"""AI Provider Abstraction - Support for multiple LLM providers."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import os
import json


class AIProvider(ABC):
    """Abstract base class for AI providers."""

    @abstractmethod
    def generate(self, prompt: str, system_prompt: str = "",
                 temperature: float = 0.1, max_tokens: int = 4096) -> str:
        """Generate completion from prompt."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is available."""
        pass

    @abstractmethod
    def get_model_name(self) -> str:
        """Get the model name."""
        pass


class MockAIProvider(AIProvider):
    """Mock AI provider for offline/development use."""

    def __init__(self):
        self.call_count = 0

    def generate(self, prompt: str, system_prompt: str = "",
                 temperature: float = 0.1, max_tokens: int = 4096) -> str:
        self.call_count += 1

        # Return structured mock responses based on prompt content
        prompt_lower = prompt.lower()

        if "verification plan" in prompt_lower:
            return self._mock_verification_plan()
        elif "assertion" in prompt_lower or "sva" in prompt_lower:
            return self._mock_assertions()
        elif "test" in prompt_lower and "uvm" not in prompt_lower:
            return self._mock_tests()
        elif "uvm" in prompt_lower:
            return self._mock_uvm()
        elif "failure" in prompt_lower or "root cause" in prompt_lower:
            return self._mock_failure_analysis()
        elif "coverage" in prompt_lower:
            return self._mock_coverage_analysis()
        else:
            return self._mock_generic()

    def _mock_verification_plan(self) -> str:
        return json.dumps({
            "items": [
                {
                    "id": "VP-AI-001",
                    "feature": "AI-Generated Feature",
                    "requirement": "AI-inferred requirement from RTL patterns",
                    "stimulus": "AI-suggested stimulus pattern",
                    "expected_behavior": "AI-predicted behavior",
                    "assertion_candidate": "AI-generated assertion",
                    "coverage_goal": "AI-identified coverage target",
                    "priority": 7,
                    "confidence": "medium",
                    "evidence": "Pattern matching in RTL",
                    "source_type": "ai-inferred"
                }
            ]
        }, indent=2)

    def _mock_assertions(self) -> str:
        return json.dumps({
            "assertions": [
                {
                    "name": "ai_generated_assertion_1",
                    "description": "AI-generated assertion for data integrity",
                    "sva_code": "// AI-generated: property p_data_integrity; @(posedge clk) disable iff (reset) valid |-> ##1 data == $past(data); endproperty",
                    "assertion_type": "concurrent",
                    "confidence": "medium",
                    "evidence": "AI pattern recognition",
                    "assumptions": "Standard data path behavior",
                    "validation_status": "REQUIRES ENGINEER VALIDATION",
                    "classification": "GENERATED"
                }
            ]
        }, indent=2)

    def _mock_tests(self) -> str:
        return json.dumps({
            "tests": [
                {
                    "name": "tb_ai_generated_test",
                    "test_type": "directed",
                    "code": "// AI-generated test\nmodule tb_ai_test;\n  // ... test code\nendmodule",
                    "verification_objective": "AI-generated test objective",
                    "target_coverage": ["ai_targeted_coverage"],
                    "target_signals": ["signal1", "signal2"]
                }
            ]
        }, indent=2)

    def _mock_uvm(self) -> str:
        return json.dumps({
            "components": [
                {
                    "component_type": "sequence_item",
                    "name": "ai_sequence_item",
                    "code": "// AI-generated UVM sequence item\nclass ai_seq_item extends uvm_sequence_item;\n  // ...\nendclass"
                }
            ]
        }, indent=2)

    def _mock_failure_analysis(self) -> str:
        return json.dumps({
            "failure_summary": "AI-analyzed failure summary",
            "facts": [
                {"fact": "Assertion failed at line 42", "source": "simulation_log", "confidence": "observed"}
            ],
            "relevant_signals": [{"name": "signal1", "value": "X"}],
            "rtl_context": {"module": "test_module", "line": 42},
            "hypotheses": [
                {"hypothesis": "Signal not initialized", "confidence": "medium", "evidence": ["X value observed"]}
            ],
            "suggested_investigation": ["Check reset logic", "Verify initialization"],
            "confidence": "medium",
            "separation_of_concerns": {
                "facts": ["Assertion failed at line 42"],
                "hypotheses": ["Signal not initialized"]
            }
        }, indent=2)

    def _mock_coverage_analysis(self) -> str:
        return json.dumps({
            "gaps": [
                {
                    "gap_type": "reachable_untested",
                    "coverage_type": "branch",
                    "description": "AI-identified uncovered branch",
                    "rtl_location": {"module": "test_module", "line": 100},
                    "suggested_test": "AI-suggested test for branch coverage"
                }
            ]
        }, indent=2)

    def _mock_generic(self) -> str:
        return json.dumps({"response": "AI mock response", "classification": "GENERATED"})

    def is_available(self) -> bool:
        return True

    def get_model_name(self) -> str:
        return "mock-ai-v0.1"


class OpenAICompatibleProvider(AIProvider):
    """OpenAI-compatible API provider."""

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None,
                 model: str = "gpt-4o"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.base_url = base_url or os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        self.model = model
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                from openai import OpenAI
                self._client = OpenAI(
                    api_key=self.api_key,
                    base_url=self.base_url
                )
            except ImportError:
                raise RuntimeError("openai package not installed. Run: pip install openai")
        return self._client

    def generate(self, prompt: str, system_prompt: str = "",
                 temperature: float = 0.1, max_tokens: int = 4096) -> str:
        if not self.is_available():
            raise RuntimeError("OpenAI provider not available - missing API key")

        client = self._get_client()
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content

    def is_available(self) -> bool:
        return self.api_key is not None and len(self.api_key) > 0

    def get_model_name(self) -> str:
        return self.model


def get_ai_provider(provider: str = "mock", **kwargs) -> AIProvider:
    """Factory function to get AI provider instance."""
    providers = {
        "mock": MockAIProvider,
        "openai": OpenAICompatibleProvider,
    }

    provider_class = providers.get(provider.lower())
    if not provider_class:
        raise ValueError(f"Unknown AI provider: {provider}. Available: {list(providers.keys())}")

    return provider_class(**kwargs)