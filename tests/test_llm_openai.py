"""Unit tests for OpenAIAnswerGenerator.

We patch the OpenAI class itself (imported into llm_openai.py) rather
than making a real call: that keeps this test offline and free, whether
the adapter is pointed at the real OpenAI API or a local Ollama server --
see docs/phase2_spec.md's test rules. What's worth testing here is this
adapter's own logic: prompt construction, history replay, and mapping
the response back into Answer/Citation.
"""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from itw_me.adapters.outbound.llm_openai import OpenAIAnswerGenerator
from itw_me.domain.models import Answer, Citation, Exchange, Question, RetrievedChunk


def _fake_response(content: str, prompt_tokens: int = 10, completion_tokens: int = 5):
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=content))],
        usage=SimpleNamespace(
            prompt_tokens=prompt_tokens, completion_tokens=completion_tokens
        ),
    )


def _build_generator(response) -> tuple[OpenAIAnswerGenerator, MagicMock]:
    fake_client = MagicMock()
    fake_client.chat.completions.create.return_value = response
    with patch(
        "itw_me.adapters.outbound.llm_openai.OpenAI", return_value=fake_client
    ):
        generator = OpenAIAnswerGenerator(model="test-model")
    return generator, fake_client


def test_generate_builds_answer_with_citations_and_token_usage():
    generator, fake_client = _build_generator(_fake_response("I work in Berlin."))
    context = [
        RetrievedChunk(
            chunk_id="c1",
            source_file="cv.md",
            text="Antoine works in Berlin.",
            score=0.9,
        )
    ]

    answer = generator.generate(Question(text="Where do you work?"), context, history=[])

    assert answer == Answer(
        text="I work in Berlin.",
        citations=(
            Citation(source_file="cv.md", chunk_id="c1", excerpt="Antoine works in Berlin."),
        ),
        input_tokens=10,
        output_tokens=5,
    )

    call_kwargs = fake_client.chat.completions.create.call_args.kwargs
    assert call_kwargs["model"] == "test-model"
    assert "[cv.md#c1]" in call_kwargs["messages"][0]["content"]
    assert call_kwargs["messages"][-1] == {
        "role": "user",
        "content": "Where do you work?",
    }


def test_generate_replays_history_as_alternating_messages():
    generator, fake_client = _build_generator(_fake_response("Second answer."))
    history = [
        Exchange(
            question=Question(text="First question?"),
            answer=Answer(text="First answer.", citations=()),
        )
    ]

    generator.generate(Question(text="Second question?"), context=[], history=history)

    messages = fake_client.chat.completions.create.call_args.kwargs["messages"]
    assert messages[1] == {"role": "user", "content": "First question?"}
    assert messages[2] == {"role": "assistant", "content": "First answer."}
    assert messages[3] == {"role": "user", "content": "Second question?"}


def test_generate_with_no_context_says_so_in_the_prompt():
    generator, fake_client = _build_generator(_fake_response("I don't know."))

    answer = generator.generate(Question(text="Anything?"), context=[], history=[])

    assert answer.citations == ()
    system_message = fake_client.chat.completions.create.call_args.kwargs["messages"][0]
    assert "No excerpts were found" in system_message["content"]


def test_constructor_defaults_api_key_when_none_given():
    with patch("itw_me.adapters.outbound.llm_openai.OpenAI") as mock_openai_cls:
        OpenAIAnswerGenerator(model="m", base_url="http://localhost:11434/v1")

    mock_openai_cls.assert_called_once_with(
        base_url="http://localhost:11434/v1", api_key="not-needed"
    )


def test_generate_opens_a_dependency_span_with_the_model_name():
    """Same trick as test_retriever_chroma.py's equivalent: patch this
    module's own `_tracer` rather than needing a real OTel provider.
    """
    generator, _ = _build_generator(_fake_response("hi"))

    fake_span_cm = MagicMock()
    fake_span_cm.__exit__.return_value = False
    with patch("itw_me.adapters.outbound.llm_openai._tracer") as fake_tracer:
        fake_tracer.start_as_current_span.return_value = fake_span_cm
        generator.generate(Question(text="Anything?"), context=[], history=[])

    fake_tracer.start_as_current_span.assert_called_once_with(
        "llm.chat.completions", attributes={"llm.model": "test-model"}
    )
