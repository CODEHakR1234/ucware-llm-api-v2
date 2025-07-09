# app/service/summary_graph_builder.py
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


class SummaryState(BaseModel):
    file_id: str
    url: str
    query: str
    chunks: Optional[List[TextChunk]] = None
    retrieved: Optional[List[TextChunk]] = None
    summary: Optional[str] = None
    cached: Optional[bool] = None           # ← hit 여부 플래그
    _cache_key: Optional[str] = None        # 내부용 (저장 시 사용)


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

    def build(self):
        g = StateGraph(SummaryState)

        # ────────── 0. 캐시 확인 ──────────
        async def check_cache(st: SummaryState):
            key = f"{st.file_id}:{hash(st.query)}"
            if (cached := self.cache.get_pdf(key)):
                st.summary = cached
                st.cached = True
                return "hit", st           # 분기 태그
            st.cached = False
            st._cache_key = key
            return "miss", st

        # ────────── 1. PDF → 청크 ──────────
        async def load_pdf(st: SummaryState):
            st.chunks = await self.loader.load(st.url)
            return st

        # ────────── 2. 벡터 DB upsert ───────
        async def embed(st: SummaryState):
            await self.store.upsert(st.chunks, st.file_id)  # type: ignore[arg-type]
            return st

        # ────────── 3. 문서 검색 ────────────
        async def retrieve(st: SummaryState):
            st.retrieved = await self.store.similarity_search(
                st.file_id, st.query, k=8
            )
            return st

        # ────────── 4. 요약 ────────────────
        async def summarize(st: SummaryState):
            st.summary = await self.summarizer.summarize(
                st.retrieved, st.query
            )  # type: ignore[arg-type]
            return st

        # ────────── 5. 캐시 저장 ────────────
        async def save_cache(st: SummaryState):
            if not st.cached:                      # miss였을 때만 저장
                self.cache.set_pdf(st._cache_key, st.summary)
            return st

        # ── 노드 등록
        g.add_node("cache", check_cache)
        g.add_node("load", load_pdf)
        g.add_node("embed", embed)
        g.add_node("retrieve", retrieve)
        g.add_node("summarize", summarize)
        g.add_node("save", save_cache)

        # ── 흐름 정의
        g.set_entry_point("cache")
        g.add_conditional_edges(
            "cache",
            {"hit": "save", "miss": "load"},
        )
        g.add_edge("load", "embed")
        g.add_edge("embed", "retrieve")
        g.add_edge("retrieve", "summarize")
        g.add_edge("summarize", "save")

        g.set_finish_point("save")

        return g.compile()

