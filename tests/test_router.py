"""
Tests for router.py's intent classification.

These mock every Gemini call, so they run instantly with no API key and no
network access — they test the routing *logic*, not whether Gemini is up.
Run with: pytest tests/
"""
from unittest.mock import MagicMock, patch

import router


# ── classify_intent_keywords: pure logic, no mocking needed ────────────────

def test_keyword_classifier_routes_scheme_question_to_rag():
    assert router.classify_intent_keywords("Am I eligible for PM-KISAN?") == "rag_agent"


def test_keyword_classifier_routes_price_question_to_price_agent():
    assert router.classify_intent_keywords("What is the wheat price trend in Indore?") == "price_agent"


def test_keyword_classifier_routes_hindi_scheme_keyword_to_rag():
    assert router.classify_intent_keywords("PMFBY योजना के बारे में बताओ") == "rag_agent"


def test_keyword_classifier_scheme_keyword_wins_even_with_price_words_present():
    # "rate" and "premium" both appear — scheme intent should still win,
    # since scheme_keywords are checked first (this is intentional priority,
    # not an accident, so the test documents that decision).
    assert router.classify_intent_keywords("PMFBY premium rate for Kharif") == "rag_agent"


def test_keyword_classifier_defaults_to_rag_when_nothing_matches():
    assert router.classify_intent_keywords("hello how are you") == "rag_agent"


# ── classify_intent: LLM path with mocked Gemini ────────────────────────────

def test_classify_intent_uses_llm_response_when_valid():
    """When Gemini returns a clean label, that's authoritative — even if the
    keyword classifier would have guessed differently."""
    mock_response = MagicMock()
    mock_response.text = "price_agent"
    with patch.object(router, "API_KEY", "dummy-key-for-test"), \
         patch("router.genai.GenerativeModel") as mock_model_cls:
        mock_model_cls.return_value.generate_content.return_value = mock_response
        # "PMFBY" would normally hit the keyword scheme-path, but the LLM
        # response should win since it came back clean.
        result = router.classify_intent("some ambiguous PMFBY-adjacent question")
        assert result == "price_agent"


def test_classify_intent_falls_back_to_keywords_on_api_error():
    with patch.object(router, "API_KEY", "dummy-key-for-test"), \
         patch("router.genai.GenerativeModel") as mock_model_cls:
        mock_model_cls.return_value.generate_content.side_effect = Exception("API down")
        result = router.classify_intent("Am I eligible for PM-KISAN?")
        assert result == "rag_agent"  # keyword fallback still gets this right


def test_classify_intent_falls_back_to_keywords_on_unrecognized_label():
    mock_response = MagicMock()
    mock_response.text = "not_a_real_label"
    with patch.object(router, "API_KEY", "dummy-key-for-test"), \
         patch("router.genai.GenerativeModel") as mock_model_cls:
        mock_model_cls.return_value.generate_content.return_value = mock_response
        result = router.classify_intent("What is the wheat price trend in Indore?")
        assert result == "price_agent"  # keyword fallback still gets this right


def test_classify_intent_skips_llm_entirely_without_api_key():
    with patch.object(router, "API_KEY", None):
        result = router.classify_intent("Am I eligible for PM-KISAN?")
        assert result == "rag_agent"


# ── route_question: end-to-end wiring, agent failures shouldn't crash ──────

def test_route_question_returns_error_dict_if_agent_raises():
    with patch.object(router, "API_KEY", None), \
         patch("router.answer_eligibility_question") as mock_agent:
        mock_agent.side_effect = Exception("boom")
        result = router.route_question("Am I eligible for PM-KISAN?")
        assert result["routed_to"] == "rag_agent"
        assert "error" in result["response"]


def test_route_question_falls_back_to_rag_if_classify_intent_itself_raises():
    with patch("router.classify_intent", side_effect=Exception("classifier crashed")):
        result = router.route_question("anything")
        assert result["routed_to"] == "rag_agent"