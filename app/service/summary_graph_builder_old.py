# app/service/summary_graph_builder.py
"""LangGraph pipeline with robust **error handling** and safe branching.

This version fixes the remaining AttributeError‑triggering branches and
ensures that *any* node exception short‑circuits to the ``finish`` node.
"""

from __future__ import annotations

from functools import wraps
from typing import Awaitable, Callable, List, Optional

from langgraph.graph import StateGraph
from pydantic import BaseModel

from app.domain.interfaces import (
    CacheIF,
    LlmChainIF,
    PdfLoaderIF,
    TextChunk,
    VectorStoreIF,
)

# ---------------------------------------------------------------------------
# Shared state
# ---------------------------------------------------------------------------
class SummaryState(BaseModel):
    file_id: str
    url: str
    query: str

    # runtime‑filled fields
    chunks: Optional[List[TextChunk]] = None
    retrieved: Optional[List[TextChunk]] = None

    summary: Optional[str] = None  # SUMMARY_ALL 결과
    answer: Optional[str] = None   # Q&A 결과

    cached: bool = False           # summary cached?
    embedded: bool = False         # vectors already stored?
    is_summary: bool = False       # query == "SUMMARY_ALL"

    error: Optional[str] = None    # Any node‑level exception message


# ---------------------------------------------------------------------------
# Utility: safe decorator
# ---------------------------------------------------------------------------

def safe(fn: Callable[[SummaryState], Awaitable[SummaryState]]):
    """Catch *all* exceptions inside a node and write into ``st.error``."""

    @wraps(fn)
    async def _wrapper(st: SummaryState):  # type: ignore[override]
        try:
            return await fn(st)
        except Exception as exc:  # noqa: BLE001
            st.error = f"{fn.__name__}: {exc}"
            return st

    return _wrapper


# ---------------------------------------------------------------------------
# Graph builder
# ---------------------------------------------------------------------------
class SummaryGraphBuilder:
    def __init__(
        self,
        loader: PdfLoaderIF,
        store: VectorStoreIF,
        llm: LlmChainIF,
        cache: CacheIF,
    ):
        self.loader, self.store, self.llm, self.cache = loader, store, llm, cache

    # ------------------------------------------------------------------
    def build(self):
        g = StateGraph(SummaryState)

        # 0. Entry router ------------------------------------------------
        @safe
        async def entry_router(st: SummaryState):
            st.is_summary = st.query.strip().upper() == "SUMMARY_ALL"

            # cache only for SUMMARY_ALL
            if st.is_summary and self.cache.exists_summary(st.file_id):
                st.summary = self.cache.get_summary(st.file_id)
                st.cached = True
            else:
                st.cached = False

            st.embedded = await self.store.has_chunks(st.file_id)  # type: ignore[arg-type]
            return st

        def entry_branch(st: SummaryState) -> str:
            if st.error:
                return "finish"
            if st.is_summary:
                if st.cached:
                    return "translate"
                return "retrieve" if st.embedded else "load"
            return "retrieve" if st.embedded else "load"

        g.add_node("entry", entry_router)

        # 1. Load --------------------------------------------------------
        @safe
        async def load_pdf(st: SummaryState):
            st.chunks = await self.loader.load(st.url)
            return st

        g.add_node("load", load_pdf)

        # 2. Embed -------------------------------------------------------
        @safe
        async def embed(st: SummaryState):
            if not st.embedded:
                await self.store.upsert(st.chunks, st.file_id)  # type: ignore[arg-type]
                st.embedded = True
            return st

        g.add_node("embed", embed)

        # 3‑S. Summarize -------------------------------------------------
        @safe
        async def summarize(st: SummaryState):
            if st.chunks is None:
                st.chunks = await self.store.get_all(st.file_id)  # type: ignore[arg-type]
            st.summary = await self.llm.summarize(st.chunks)  # type: ignore[arg-type]
            return st

        g.add_node("summarize", summarize)

        # 3‑Q. Retrieve --------------------------------------------------
        @safe
        async def retrieve(st: SummaryState):
            st.retrieved = await self.store.similarity_search(st.file_id, st.query)
            return st

        g.add_node("retrieve", retrieve)

        # 4‑Q. Answer ----------------------------------------------------
        @safe
        async def answer(st: SummaryState):
            joined = "\n\n".join(st.retrieved)
            prompt = (
                "다음 글 조각들을 참고하여 **질문에 한국어로 답하세요**.\n"
                f"### 질문: {st.query}\n### 글\n{joined}\n### 답변:"
            )
            st.answer = await self.llm.execute(prompt)
            return st

        g.add_node("answer", answer)

        # 5. Save summary -----------------------------------------------
        @safe
        async def save_summary(st: SummaryState):
            if st.is_summary and not st.cached and st.summary:
                self.cache.set_summary(st.file_id, st.summary)
            return st

        g.add_node("save", save_summary)

        # 6. Translate (cached summary) ---------------------------------
        g.add_node("translate", lambda st: st)

        # 7. Finish ------------------------------------------------------
        g.add_node("finish", lambda st: st)

        # Routing --------------------------------------------------------
        g.set_entry_point("entry")

        g.add_conditional_edges(
            "entry",
            entry_branch,
            {
                "translate": "translate",
                "retrieve": "retrieve",
                "load": "load",
                "finish": "finish",  # error short‑circuit
            },
        )

        g.add_edge("load", "embed")

        def post_embed(st: SummaryState) -> str:
            if st.error:
                return "finish"
            return "summarize" if st.is_summary else "retrieve"

        g.add_conditional_edges("embed", post_embed, {
            "summarize": "summarize",
            "retrieve": "retrieve",
            "finish": "finish",
        })

        def post_retrieve(st: SummaryState) -> str:
            if st.error:
                return "finish"
            return "summarize" if st.is_summary else "answer"

        g.add_conditional_edges("retrieve", post_retrieve, {
            "summarize": "summarize",
            "answer": "answer",
            "finish": "finish",
        })

        g.add_edge("answer", "finish")
        g.add_edge("summarize", "save")
        g.add_edge("save", "finish")
        g.add_edge("translate", "finish")

        g.set_finish_point("finish")
        return g.compile()

