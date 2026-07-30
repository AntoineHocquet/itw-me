"""TODO(antoine): LLM implementation of AnswerGenerator.

Suggested approach (any OpenAI-compatible API works, including a
local Ollama server if you want zero cost):
- Build the prompt: system message ("You are Antoine's CV speaking
  in first person...") + retrieved chunks as context + history + question.
- Call the chat completions endpoint.
- Fill Answer.input_tokens / output_tokens from the usage field of
  the response; you will want these in phase 3 for metrics.
- Build Citations from the chunks you actually put in the prompt.

Same rule as the retriever: the openai import lives here and only here.
"""

from itw_me.domain.models import Answer, Question, RetrievedChunk
from itw_me.domain.ports import AnswerGenerator


class OpenAIAnswerGenerator(AnswerGenerator):
    def __init__(self, model: str = "gpt-4o-mini") -> None:
        self._model = model

    def generate(
        self,
        question: Question,
        context: list[RetrievedChunk],
        history: list,
    ) -> Answer:
        raise NotImplementedError
