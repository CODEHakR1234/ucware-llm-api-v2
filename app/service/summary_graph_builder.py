# app/service/summary_graph_builder.py
"""LangGraph for PDF Q&A (chat) **and** full‑document summarization.

Branching logic (v3)
-------------------
* **EntryRouter** figures out three booleans: ``is_summary``, ``cached``,
  ``embedded`` and yields one of three literal branch keys:

    | is_summary | cached | embedded | branch key |
    |------------|--------|----------|------------|
    | ✓          | ✓      | *        | ``translate`` |
    | ✓          | ✗      | ✓        | ``retrieve``  |
    | ✓          | ✗      | ✗        | ``load``      |
    | ✗          | —      | ✓        | ``retrieve``  |
    | ✗          | —      | ✗        | ``load``      |

* After **retrieve**, we examine ``is_summary`` **again**:
    * ✓ → ``summarize``
    * ✗ → ``answer``

* The rest is unchanged: ``load → embed (if needed)`` and two terminal paths:
    * **summary**   → ``summarize → save → finish``
    * **Q&A chat** → ``answer → finish``

State
-----
```python
class SummaryState(BaseModel):
    file_id: str; url: str; query: str
    chunks: list[str] | None = None
    retrieved: list[str] | None = None
    summary: str | None = None     # SUMMARY_ALL 결과
    answer: str | None = None      # Q&A 결과
    cached: bool = False
    embedded: bool = False
    is_summary: bool = False
```
"""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel
from langgraph.graph import StateGraph

from app.domain.interfaces import (
    PdfLoaderIF,
    VectorStoreIF,
    LlmChainIF,
    CacheIF,
    TextChunk,
)

# ---------------------------------------------------------------------------
# Shared state definition
# ---------------------------------------------------------------------------
class SummaryState(BaseModel):
    file_id: str
    url: str
    query: str

    # runtime‑filled fields
    chunks: Optional[List[TextChunk]] = None
    retrieved: Optional[List[TextChunk]] = None

    summary: Optional[str] = None  # "SUMMARY_ALL" 결과
    answer: Optional[str] = None   # Q&A 결과

    cached: bool = False           # summary cached?
    embedded: bool = False         # vectors already stored?
    is_summary: bool = False       # query == "SUMMARY_ALL"


# ---------------------------------------------------------------------------
# Graph builder
# ---------------------------------------------------------------------------
class SummaryGraphBuilder:
    def __init__(
        self,
        loader: PdfLoaderIF,
        store: VectorStoreIF,
        summarizer: LlmChainIF,
        cache: CacheIF,
    ):
        self.loader, self.store, self.summarizer, self.cache = (
            loader,
            store,
            summarizer,
            cache,
        )

    # ------------------------------------------------------------------
    # Graph assembly
    # ------------------------------------------------------------------
    def build(self):
        g = StateGraph(SummaryState)

        # --------------------------------------------------------------
        # 0. Entry router
        # --------------------------------------------------------------
        async def entry_router(st: SummaryState):
            st.is_summary = st.query.strip().upper() == "SUMMARY_ALL"

            # 0‑1) cache check only for SUMMARY_ALL
            if st.is_summary and self.cache.exists_summary(st.file_id):
                st.summary = self.cache.get_summary(st.file_id)
                st.cached = True
            else:
                st.cached = False

            # 0‑2) vector existence
            st.embedded = await self.store.has_chunks(st.file_id)  # type: ignore[arg-type]
            return st  # used by branch fn

        def entry_branch(st: SummaryState) -> str:
            if st.is_summary:
                if st.cached:
                    return "translate"          # summary cached → translate node
                return "retrieve" if st.embedded else "load"
            # --- Q&A path ---
            return "retrieve" if st.embedded else "load"

        g.add_node("entry", entry_router)

        # --------------------------------------------------------------
        # 1. Load PDF → chunks
        # --------------------------------------------------------------
        async def load_pdf(st: SummaryState):
            st.chunks = await self.loader.load(st.url)
            return st

        g.add_node("load", load_pdf)

        # --------------------------------------------------------------
        # 2. Embed (upsert) if not already
        # --------------------------------------------------------------
        async def embed(st: SummaryState):
            if not st.embedded:  # only when needed
                await self.store.upsert(st.chunks, st.file_id)  # type: ignore[arg-type]
                st.embedded = True
            return st

        g.add_node("embed", embed)

        # --------------------------------------------------------------
        # 3‑S. Summarize full doc
        # --------------------------------------------------------------
        async def summarize(st: SummaryState):
            # obtain chunks if they came from VDB
            if st.chunks is None:
                docs = await self.store.get_all(st.file_id)  # type: ignore[arg-type]
                st.chunks = docs
            st.summary = await self.summarizer.summarize(st.chunks)  # type: ignore[arg-type]
            return st

        g.add_node("summarize", summarize)

        # --------------------------------------------------------------
        # 3‑Q. Retrieve relevant chunks
        # --------------------------------------------------------------
        async def retrieve(st: SummaryState):
            st.retrieved = await self.store.similarity_search(
                st.file_id, st.query, k=8
            )
            return st

        g.add_node("retrieve", retrieve)

        # --------------------------------------------------------------
        # 4‑Q. LLM answer
        # --------------------------------------------------------------
        async def answer(st: SummaryState):
            joined = "\n\n".join(st.retrieved)
            prompt = (
                "다음 글 조각들을 참고하여 **질문에 한국어로 답하세요**.\n"
                f"### 질문: {st.query}\n### 글\n{joined}\n### 답변:"
            )
            st.answer = await self.summarizer.execute(prompt)
            return st

        g.add_node("answer", answer)

        # --------------------------------------------------------------
        # 5. Save summary to cache (only SUMMARY_ALL & not cached)
        # --------------------------------------------------------------
        async def save_summary(st: SummaryState):
            if st.is_summary and not st.cached and st.summary:
                self.cache.set_summary(st.file_id, st.summary)
            return st

        g.add_node("save", save_summary)

        # --------------------------------------------------------------
        # 6. Translate (no‑op placeholder)
        # --------------------------------------------------------------
        g.add_node("translate", lambda st: st)  # could be i18n step later

        # --------------------------------------------------------------
        # Entry & routing edges
        # --------------------------------------------------------------
        g.set_entry_point("entry")

        g.add_conditional_edges(
            "entry",
            entry_branch,
            {
                "translate": "translate",
                "retrieve": "retrieve",
                "load": "load",
            },
        )

        # load → embed → cond (summary vs qa)
        g.add_edge("load", "embed")

        def post_embed_branch(st: SummaryState) -> str:
            return "summarize" if st.is_summary else "retrieve"

        g.add_conditional_edges("embed", post_embed_branch, {
            "summarize": "summarize",
            "retrieve": "retrieve",
        })

        # After retrieve we decide again (summary vs qa)
        def post_retrieve_branch(st: SummaryState) -> str:
            return "summarize" if st.is_summary else "answer"

        g.add_conditional_edges("retrieve", post_retrieve_branch, {
            "summarize": "summarize",
            "answer": "answer",
        })

        # qa path
        g.add_edge("answer", "finish")

        # summary path
        g.add_edge("summarize", "save")
        g.add_edge("save", "finish")

        # translate path (cached summary)
        g.add_edge("translate", "finish")

        # finish node (no‑op)
        g.add_node("finish", lambda st: st)
        g.set_finish_point("finish")

        # -------------------------
        return g.compile()

