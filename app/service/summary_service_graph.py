# app/service/summary_service_graph.py
from app.infra.pdf_loader import PdfLoader
from app.infra.vector_store import VectorStore
from app.infra.summarizer import StuffSummarizer
from app.infra.cache_store import CacheStore          
from app.domain.interfaces import CacheIF
from .summary_graph_builder import SummaryGraphBuilder, SummaryState

# ──────────────────────────────────────────────
# create graph only once at compile time
# ──────────────────────────────────────────────
_builder_singleton = SummaryGraphBuilder(
    PdfLoader(),
    VectorStore(),
    StuffSummarizer(),
    CacheStore(),
)
_compiled_graph = _builder_singleton.build()


class SummaryServiceGraph:
    """A very thin facade between the controller and the graph. (Uses a singleton graph)"""

    def __init__(self):
        self.graph = _compiled_graph   # compiled graph shared

    async def generate(self, file_id: str, pdf_url: str, query: str):
        result = await self.graph.ainvoke(
            SummaryState(file_id=file_id, url=pdf_url, query=query)
        )
        return {
            "file_id": file_id,
            "summary": result["summary"],
            "cached": result["cached"],
        }


# ---- FastAPI DI provider ----
_service_singleton = SummaryServiceGraph()  

def get_summary_service_graph() -> SummaryServiceGraph:
    """FastAPI Depends용 싱글턴 반환"""
    return _service_singleton
