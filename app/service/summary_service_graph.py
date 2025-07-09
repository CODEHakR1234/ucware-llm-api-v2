# app/service/summary_service_graph.py
from app.infra.pdf_loader import PdfLoader
from app.infra.vector_store import VectorStore
from app.infra.summarizer import MapReduceSummarizer
from app.infra.cache_store import CacheStore          
from app.domain.interfaces import CacheIF
from .summary_graph_builder import SummaryGraphBuilder, SummaryState

# ──────────────────────────────────────────────
# 1. 그래프 컴파일을 모듈 로드 시 단 한 번만 수행
# ──────────────────────────────────────────────
_builder_singleton = SummaryGraphBuilder(
    PdfLoader(),
    VectorStore(),
    MapReduceSummarizer(),
    CacheStore(),
)
_compiled_graph = _builder_singleton.build()


class SummaryServiceGraph:
    """컨트롤러-그래프 사이의 정말 얇은 퍼사드.(싱글턴 그래프 사용)"""

    def __init__(self, graph_builder: SummaryGraphBuilder):
        self.graph = _compiled_graph   # 이미 컴파일된 그래프 공유

    async def generate(self, file_id: str, pdf_url: str, query: str):
        state = await self.graph.ainvoke(
            SummaryState(file_id=file_id, url=pdf_url, query=query)
        )
        return {
            "file_id": file_id,
            "summary": state.summary,
            "cached": state.cached,
        }


# ---- FastAPI DI provider ----
_service_singleton = SummaryServiceGraph()   # 요청마다 새로 만들 필요 X

def get_summary_service_graph() -> SummaryServiceGraph:
    """FastAPI Depends용 싱글턴 반환"""
    return _service_singleton
