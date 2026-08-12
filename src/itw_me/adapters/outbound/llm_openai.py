"""OpenAI(-compatible) implementation of AnswerGenerator.

The openai client works against any server that speaks its wire format --
that includes Ollama, which exposes an OpenAI-compatible endpoint. This
adapter only knows "some chat-completions endpoint"; which server that
actually is is a composition-root decision (see container.py), passed in
via `base_url`. That is what makes the phase-2 decision -- Ollama by
default for zero-cost development, real OpenAI as an opt-in -- a config
change instead of a code change.

Every openai import stays in this file. If it leaks into domain/ or
application/, the hexagon is broken.

Phase 5 note: same reasoning as retriever_chroma.py's "chroma.query"
span -- this file's "llm.chat.completions" span is vendor-specific
(tagged with the model name), so it lives directly in this concrete
adapter rather than in the generic TracedAnswerGenerator decorator. It
nests inside "generate" automatically, for the same call-order reason.
"""

from openai import OpenAI
from opentelemetry import trace

from itw_me.domain.models import Answer, Citation, Question, RetrievedChunk
from itw_me.domain.ports import AnswerGenerator

_SYSTEM_PROMPT = (
    "You are Antoine, speaking to a visitor in the first person. Answer "
    "ONLY using the excerpts below, which are drawn from your own CV and "
    "biography. If the excerpts do not contain the answer, say plainly "
    "that you don't know or that it isn't covered in your notes -- never "
    "invent facts about yourself."
)

_tracer = trace.get_tracer("itw_me")


class OpenAIAnswerGenerator(AnswerGenerator):
    def __init__(
        self,
        model: str,
        base_url: str | None = None,
        api_key: str | None = None,
    ) -> None:
        self._model = model
        # The openai client raises at construction time if api_key is
        # falsy, even against servers (Ollama) that ignore it entirely --
        # so a dummy placeholder stands in when none is configured.
        self._client = OpenAI(base_url=base_url, api_key=api_key or "not-needed")

    def generate(
        self,
        question: Question,
        context: list[RetrievedChunk],
        history: list,
    ) -> Answer:
        messages = [
            {"role": "system", "content": self._build_system_message(context)}
        ]
        # history is list[Exchange] (see domain/models.py); replayed as
        # alternating user/assistant turns so the model sees the
        # conversation so far, not just the latest question in isolation.
        for exchange in history:
            messages.append({"role": "user", "content": exchange.question.text})
            if exchange.answer is not None:
                messages.append(
                    {"role": "assistant", "content": exchange.answer.text}
                )
        messages.append({"role": "user", "content": question.text})

        # Attribute is the model name only -- never `messages`, which
        # contains this visitor's actual question and every prior turn's
        # text. Same discipline as retriever_chroma.py's span.
        with _tracer.start_as_current_span(
            "llm.chat.completions", attributes={"llm.model": self._model}
        ):
            response = self._client.chat.completions.create(
                model=self._model,
                messages=messages,
            )

        # Citations reflect exactly the chunks placed in the prompt above
        # (i.e. all of `context`) -- if retrieval returned nothing, there
        # is nothing to cite, which is the honest answer.
        citations = tuple(
            Citation(
                source_file=chunk.source_file,
                chunk_id=chunk.chunk_id,
                excerpt=chunk.text,
            )
            for chunk in context
        )

        usage = response.usage
        return Answer(
            text=response.choices[0].message.content or "",
            citations=citations,
            input_tokens=usage.prompt_tokens if usage else 0,
            output_tokens=usage.completion_tokens if usage else 0,
        )

    @staticmethod
    def _build_system_message(context: list[RetrievedChunk]) -> str:
        if not context:
            return f"{_SYSTEM_PROMPT}\n\nNo excerpts were found for this question."

        # Each excerpt is labeled [source_file#chunk_id] -- the same
        # format api.py uses for the Citations it returns over HTTP, so a
        # visitor (or the model, if asked to cite) sees one consistent
        # reference scheme end to end.
        excerpts = "\n\n".join(
            f"[{chunk.source_file}#{chunk.chunk_id}] {chunk.text}"
            for chunk in context
        )
        return f"{_SYSTEM_PROMPT}\n\nExcerpts:\n{excerpts}"
