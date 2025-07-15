# app/vectordb/vector_db.py
from __future__ import annotations

import os
import threading
from datetime import datetime
from functools import lru_cache
from typing import List, Union

import chromadb
from chromadb.config import Settings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_community.embeddings import HuggingFaceEmbeddings
from zoneinfo import ZoneInfo

from app.cache.cache_db import get_cache_db   # 삭제 로그용

# ─────────────────────── 환경 설정 ──────────────────────────────
CHUNK_SIZE      = 500
CHUNK_OVERLAP   = 50
_BATCH_SIZE     = 500

CHROMA_HOST     = os.getenv("CHROMA_HOST", "localhost")
CHROMA_PORT     = int(os.getenv("CHROMA_PORT", "9000"))

LLM_PROVIDER        = os.getenv("LLM_PROVIDER", "openai")
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME")

_PERSIST_DIR    = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")

# ──────────────────── Embedding 선택 ────────────────────────────
def _get_embedding_model():
    if LLM_PROVIDER.lower() == "hf":
        return HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL_NAME,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )
    return OpenAIEmbeddings(model=EMBEDDING_MODEL_NAME)

# ──────────────────── VectorDB 클래스 ───────────────────────────
class VectorDB:
    def __init__(self) -> None:
        self.embeddings = _get_embedding_model()
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            length_function=len,
        )

        self._lock   = threading.RLock()
        self._client = None                       # lazy 연결

    # ------------- Chroma client (lazy) ------------------------
    @property
    def client(self) -> chromadb.HttpClient | None:
        if self._client is None:
            try:
                print(f"[VectorDB] Connecting → {CHROMA_HOST}:{CHROMA_PORT}")
                self._client = chromadb.HttpClient(
                    host=CHROMA_HOST,
                    port=CHROMA_PORT,
                )
                print("[VectorDB] ✅ Chroma connection OK")
            except Exception as e:
                print(f"[VectorDB] ❌ Chroma connect failed: {e}")
                self._client = None
        return self._client

    # ------------- 내부 헬퍼 -------------------------------
    def _get_collection_name(self, file_id: str) -> str:
        return file_id

    def _get_vectorstore(self, file_id_or_col: str) -> Chroma:
        """file_id 또는 이미 collection_name 이 들어와도 동작."""
        if self.client is None:
            raise RuntimeError("Chroma client not available")
        return Chroma(
            client=self.client,
            collection_name=file_id_or_col,
            embedding_function=self.embeddings,
            persist_directory=_PERSIST_DIR,
        )

    # ------------- CRUD 메서드 ----------------------------
    def store(self, content: Union[str, List[str]], file_id: str) -> None:
        """`content` 가 문자열이면 → 청크로 분할, list[str] 이면 그대로 저장."""
        try:
            chunks = (
                self.text_splitter.split_text(content)
                if isinstance(content, str)
                else content
            )
            if not chunks:
                print(f"[VectorDB.store] ⚠️ no chunks for {file_id}")
                return

            today = datetime.now(ZoneInfo("Asia/Seoul")).strftime("%Y-%m-%d")
            docs: List[Document] = [
                Document(
                    page_content=ck,
                    metadata={
                        "file_id": file_id,
                        "chunk_index": idx,
                        "date": today,
                    },
                )
                for idx, ck in enumerate(chunks)
            ]

            vs = self._get_vectorstore(self._get_collection_name(file_id))
            with self._lock:
                for i in range(0, len(docs), _BATCH_SIZE):
                    try:
                        vs.add_documents(docs[i : i + _BATCH_SIZE])
                    except Exception as e:
                        print(f"[VectorDB.store] batch {i//_BATCH_SIZE} fail: {e}")

            print(f"[VectorDB.store] ✅ stored {len(docs)} docs for {file_id}")

        except Exception as e:
            print(f"[VectorDB.store] ❌ {e}")

    def get_docs(self, file_id: str, query: str, k: int = 8) -> List[Document]:
        try:
            return self._get_vectorstore(self._get_collection_name(file_id)).similarity_search(query, k=k)
        except Exception as e:
            print(f"[VectorDB.get_docs] ❌ {e}")
            return []

    def get_all_chunks(self, file_id: str) -> List[Document]:
        """chunk_index 기준 정렬 반환."""
        try:
            col = self.client.get_collection(self._get_collection_name(file_id))  # type: ignore
            data = col.get(include=["documents", "metadatas"])
            docs_raw  = data.get("documents", [])
            metas_raw = data.get("metadatas", [{}] * len(docs_raw))

            items = sorted(
                zip(docs_raw, metas_raw),
                key=lambda x: x[1].get("chunk_index", 0),
            )
            return [Document(page_content=d, metadata=m) for d, m in items]
        except Exception as e:
            print(f"[VectorDB.get_all_chunks] ❌ {e}")
            return []

    def has_chunks(self, file_id: str) -> bool:
        try:
            return self.client.get_collection(self._get_collection_name(file_id)).count() > 0  # type: ignore
        except Exception:
            return False

    def delete_document(self, file_id: str) -> bool:
        try:
            with self._lock:
                self.client.delete_collection(self._get_collection_name(file_id))  # type: ignore
            self._log_vector_deletion(file_id)
            return True
        except Exception as e:
            print(f"[VectorDB.delete_document] ❌ {e}")
            return False

    def list_stored_documents(self) -> List[str]:
        try:
            return [c.name for c in self.client.list_collections()]  # type: ignore
        except Exception as e:
            print(f"[VectorDB.list_stored_documents] ❌ {e}")
            return []

    # ------------- 유지보수/모니터링 -----------------------
    def cleanup_unused_vectors(self) -> List[str]:
        deleted: List[str] = []
        cache = get_cache_db()
        for fid in self.list_stored_documents():
            if not cache.get_pdf(fid) and self.delete_document(fid):
                deleted.append(fid)
        return deleted

    def is_chroma_alive(self) -> bool:
        try:
            self.client.heartbeat()         # type: ignore
            return True
        except Exception:
            return False

    def delete_all_vectors(self) -> int:
        cnt = 0
        for fid in self.list_stored_documents():
            if self.delete_document(fid):
                cnt += 1
        return cnt

    def get_vectors_by_date(self, date_str: str) -> List[str]:
        matches = set()
        for fid in self.list_stored_documents():
            try:
                docs = self._get_vectorstore(fid).similarity_search("dummy", k=1)
                if any(d.metadata.get("date") == date_str for d in docs):
                    matches.add(fid)
            except Exception:
                pass
        return list(matches)

    def get_memory_estimate(self) -> dict:
        size = self._get_directory_size(_PERSIST_DIR)
        return {
            "base_path": _PERSIST_DIR,
            "disk_usage_bytes": size,
            "disk_usage_mb": round(size / (1024 * 1024), 2),
        }

    # ------------- 내부 유틸 ------------------------------
    def _get_directory_size(self, path: str) -> int:
        total = 0
        for root, _, files in os.walk(path):
            for fn in files:
                fp = os.path.join(root, fn)
                if os.path.isfile(fp):
                    total += os.path.getsize(fp)
        return total

    def _log_vector_deletion(self, file_id: str):
        try:
            r = get_cache_db().r
            now = datetime.now(ZoneInfo("Asia/Seoul"))
            key = f"vector:deleted:{now:%Y-%m-%d}"
            r.rpush(key, f"{file_id}|{now.isoformat()}")
        except Exception:
            pass


# ────────────────── 싱글턴 getter ───────────────────────────────
@lru_cache(maxsize=1)
def get_vector_db() -> "VectorDB":
    return VectorDB()

