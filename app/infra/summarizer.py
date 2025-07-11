# app/infra/summarizer.py
"""
StuffSummarizer rewritten to use LangChain Expression Language (LCEL).
Replaces the deprecated `LLMChain` class with the composable
`prompt | llm | StrOutputParser()` pipeline while keeping the public
interface unchanged.
"""

from typing import List

from langchain_core.prompts import PromptTemplate  # LCEL-friendly prompt
from langchain_core.output_parsers import StrOutputParser

from app.utils.llm_factory import get_llm_instance
from app.domain.interfaces import LlmChainIF, TextChunk

# -----------------------------------------------------------------------------
# Prompt
# -----------------------------------------------------------------------------
SUMMARY_PROMPT = PromptTemplate(
    template=(
        "다음 글 조각들을 참고하여 **질문에 한국어로 답하세요**.\n"
        "### 질문: {question}\n"
        "### 글\n{docs}\n"
        "### 답변:"
    ),
    input_variables=["docs", "question"],
)

# -----------------------------------------------------------------------------
# Summarizer
# -----------------------------------------------------------------------------
class StuffSummarizer(LlmChainIF):
    """Summarizes chunks *docs* to answer *query* in Korean.

    The class now builds its pipeline with LCEL instead of the deprecated
    :class:`langchain.chains.LLMChain`.
    """

    def __init__(self) -> None:
        llm = get_llm_instance(temperature=0.3)

        # LCEL: prompt | llm | parser → returns str
        self.chain = SUMMARY_PROMPT | llm | StrOutputParser()

    # ---------------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------------
    async def execute(self, docs: List[TextChunk], query: str) -> str:  # noqa: D401
        """Return a Korean answer to *query* based on the provided *docs*."""
        joined = "\n\n".join(docs)  # RAG‑selected chunks merged

        # LCEL chains support async via ``ainvoke``
        answer: str = await self.chain.ainvoke({"docs": joined, "question": query})
        return answer.strip()

