"""
Tests for rag_agent.py's retrieval + generation pipeline.

These mock genai.embed_content, genai.GenerativeModel, and the ChromaDB
collection — so they test *our* logic (does a failed embed return [] instead
of crashing, does retrieved context actually make it into the prompt) rather
than whether Google's API or the local chroma_db/ folder happens to be
reachable when you run pytest.
"""
from unittest.mock import MagicMock, patch

import rag_agent


# ── retrieve_chunks ──────────────────────────────────────────────────────

def test_retrieve_chunks_returns_documents_from_chromadb_query():
    fake_collection = MagicMock()
    fake_collection.query.return_value = {
        "documents": [["chunk about PMFBY premiums", "chunk about PM-KISAN eligibility"]]
    }
    with patch.object(rag_agent, "API_KEY", "dummy-key-for-test"), \
         patch.object(rag_agent, "_get_collection", return_value=fake_collection), \
         patch("rag_agent.genai.embed_content", return_value={"embedding": [0.1, 0.2, 0.3]}):
        result = rag_agent.retrieve_chunks("What is the PMFBY premium?")
        assert result == ["chunk about PMFBY premiums", "chunk about PM-KISAN eligibility"]


def test_retrieve_chunks_returns_empty_list_without_api_key():
    """No key means no embedding call at all — should short-circuit to [],
    not attempt a call that would fail anyway."""
    with patch.object(rag_agent, "API_KEY", None):
        assert rag_agent.retrieve_chunks("anything") == []


def test_retrieve_chunks_returns_empty_list_if_embedding_call_fails():
    """This is the exact failure mode that broke build_index.py earlier
    (wrong model name -> 404). Retrieval should degrade to [], not crash
    the whole /api/ask request."""
    with patch.object(rag_agent, "API_KEY", "dummy-key-for-test"), \
         patch("rag_agent.genai.embed_content", side_effect=Exception("404 model not found")):
        assert rag_agent.retrieve_chunks("What is the PMFBY premium?") == []


def test_retrieve_chunks_returns_empty_list_if_collection_unavailable():
    """Covers the case where chroma_db/ hasn't been built yet (or was built
    with a different embedding dimension) — get_collection() raises."""
    with patch.object(rag_agent, "API_KEY", "dummy-key-for-test"), \
         patch.object(rag_agent, "_get_collection", side_effect=Exception("collection not found")):
        assert rag_agent.retrieve_chunks("anything") == []


# ── generate_scheme_answer ───────────────────────────────────────────────

def test_generate_scheme_answer_includes_retrieved_context_in_prompt():
    """The whole point of this rewrite: retrieved chunks must actually reach
    the model, not just get computed and discarded."""
    mock_response = MagicMock()
    mock_response.text = "Some answer"
    captured_prompt = {}

    def fake_generate_content(prompt, **kwargs):
        captured_prompt["value"] = prompt
        return mock_response

    with patch.object(rag_agent, "API_KEY", "dummy-key-for-test"), \
         patch("rag_agent.genai.GenerativeModel") as mock_model_cls:
        mock_model_cls.return_value.generate_content.side_effect = fake_generate_content
        rag_agent.generate_scheme_answer(
            "What is the PMFBY premium?",
            ["What it costs the farmer: 2% for Kharif crops"],
            language="en",
        )
        assert "2% for Kharif crops" in captured_prompt["value"]


def test_generate_scheme_answer_tells_model_context_is_missing_when_chunks_empty():
    """When retrieval comes back empty, the prompt should say so explicitly
    rather than silently answering as if it had grounded context."""
    mock_response = MagicMock()
    mock_response.text = "Some answer"
    captured_prompt = {}

    def fake_generate_content(prompt, **kwargs):
        captured_prompt["value"] = prompt
        return mock_response

    with patch.object(rag_agent, "API_KEY", "dummy-key-for-test"), \
         patch("rag_agent.genai.GenerativeModel") as mock_model_cls:
        mock_model_cls.return_value.generate_content.side_effect = fake_generate_content
        rag_agent.generate_scheme_answer("What is the PMFBY premium?", [], language="en")
        assert "No reference document context was available" in captured_prompt["value"]


def test_generate_scheme_answer_falls_back_gracefully_if_generation_fails():
    with patch.object(rag_agent, "API_KEY", "dummy-key-for-test"), \
         patch("rag_agent.genai.GenerativeModel") as mock_model_cls:
        mock_model_cls.return_value.generate_content.side_effect = Exception("API down")
        result = rag_agent.generate_scheme_answer("anything", [], language="hi")
        assert "क्षमा करें" in result  # Hindi fallback string, not a crash


# ── answer_eligibility_question: the public contract router.py depends on ──

def test_answer_eligibility_question_returns_expected_shape():
    with patch.object(rag_agent, "retrieve_chunks", return_value=["some chunk"]), \
         patch.object(rag_agent, "generate_scheme_answer", return_value="some answer"):
        result = rag_agent.answer_eligibility_question("Am I eligible for PM-KISAN?", "en")
        assert result == {
            "question": "Am I eligible for PM-KISAN?",
            "retrieved_chunks": ["some chunk"],
            "answer": "some answer",
        }