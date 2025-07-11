# app/domain/interfaces.py
from abc import ABC, abstractmethod
from typing import List, Optional, Protocol

TextChunk = str


class PdfLoaderIF(Protocol):
    @abstractmethod
    async def load(self, url: str) -> List[TextChunk]: ...


class VectorStoreIF(Protocol):
    @abstractmethod
    async def upsert(self, chunks: List[TextChunk], doc_id: str) -> None: ...

    @abstractmethod
    async def similarity_search(self, doc_id: str, query: str, k: int = 5) -> List[TextChunk]: ...

class LlmChainIF(Protocol):
    @abstractmethod
    async def execute(self, docs: List[TextChunk], query: str) -> str: ...


class CacheIF(Protocol):
    """요약 결과 캐싱을 위한 최소 계약(Port)"""

    @abstractmethod
    def get_pdf(self, key: str) -> Optional[str]: ...

    @abstractmethod
    def set_pdf(self, key: str, summary: str) -> None: ...

