"""Tests for the Mock LLM provider."""

import pytest

from src.llm.mock_provider import MockLLMProvider
from src.llm.factory import create_llm_provider
from src.config import ExperimentConfig


class TestMockLLMProvider:
    """Tests for MockLLMProvider."""

    def test_default_response(self, mock_llm):
        response = mock_llm.generate("Hello")
        assert response.content == "Mock response content."
        assert response.model == "mock-model"
        assert response.latency_ms > 0

    def test_response_queue(self):
        llm = MockLLMProvider(response_queue=["response 1", "response 2", "response 3"])
        assert llm.generate("a").content == "response 1"
        assert llm.generate("b").content == "response 2"
        assert llm.generate("c").content == "response 3"
        # Falls back to default
        assert llm.generate("d").content == "Mock LLM response."

    def test_response_function(self):
        llm = MockLLMProvider(response_fn=lambda p: f"echo: {p}")
        response = llm.generate("test prompt")
        assert response.content == "echo: test prompt"

    def test_call_recording(self, mock_llm):
        mock_llm.generate("prompt 1")
        mock_llm.generate("prompt 2")
        assert len(mock_llm.call_history) == 2
        assert mock_llm.call_history[0]["prompt"] == "prompt 1"
        assert mock_llm.call_history[1]["prompt"] == "prompt 2"

    def test_metrics_tracking(self, mock_llm):
        mock_llm.generate("test")
        mock_llm.generate("test")
        assert mock_llm.call_count == 2
        assert mock_llm.total_tokens > 0
        assert mock_llm.total_latency_ms > 0

    def test_reset(self, mock_llm):
        mock_llm.generate("test")
        mock_llm.reset()
        assert len(mock_llm.call_history) == 0
        assert mock_llm.call_count == 0

    def test_get_last_prompt(self, mock_llm):
        mock_llm.generate("first")
        mock_llm.generate("second")
        assert mock_llm.get_last_prompt() == "second"

    def test_add_responses(self):
        llm = MockLLMProvider()
        llm.add_responses(["a", "b"])
        assert llm.generate("x").content == "a"
        assert llm.generate("x").content == "b"

    def test_token_estimation(self, mock_llm):
        response = mock_llm.generate("a" * 100)  # 100 chars ≈ 25 tokens
        assert response.prompt_tokens == 25
        assert response.total_tokens > 0


class TestLLMFactory:
    """Tests for the LLM factory."""

    def test_create_mock_provider(self):
        config = ExperimentConfig.load(
            overrides={"llm": {"provider": "mock", "model": "test-model"}}
        )
        provider = create_llm_provider(config)
        assert isinstance(provider, MockLLMProvider)
        assert provider.model == "test-model"

    def test_unknown_provider_raises(self):
        config = ExperimentConfig.load(
            overrides={"llm": {"provider": "nonexistent"}}
        )
        with pytest.raises(ValueError, match="Unknown LLM provider"):
            create_llm_provider(config)
