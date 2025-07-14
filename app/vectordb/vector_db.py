# app/vectordb/vector_db.py

import os
import threading
from functools import lru_cache
from typing import List

import chromadb
from chromadb.config import Settings
from app.cache.cache_db import get_cache_db
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from datetime import datetime

from zoneinfo import ZoneInfo
# ───────── 설정 상수 ───────────────────────────────
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50

CHROMA_HOST = os.getenv("CHROMA_HOST", "chroma")
CHROMA_PORT = int(os.getenv("CHROMA_PORT", "8000"))

print(f"[DEBUG] CHROMA_HOST={CHROMA_HOST}, CHROMA_PORT={CHROMA_PORT}")
class VectorDB:
    def __init__(self) -> None:
        self.embeddings = OpenAIEmbeddings()
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            length_function=len,
        )
        self._lock = threading.RLock()
        self._client = None  # Lazy 초기화

    @property
    def client(self):
        if self._client is None:
            try:
                print(f"[VectorDB] Connecting to Chroma at {CHROMA_HOST}:{CHROMA_PORT}")
                self._client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
                print("[VectorDB] ✅ Chroma connection successful")
            except Exception as e:
                print(f"[VectorDB.client] ❌ Chroma 연결 실패: {e}")
                self._client = None
        return self._client

    def _get_collection_name(self, file_id: str) -> str:
        return file_id

    def _get_vectorstore(self, collection_name: str) -> Chroma:
        if self.client is None:
            raise RuntimeError("Chroma 클라이언트가 연결되지 않았습니다.")
        return Chroma(
            client=self.client,
            collection_name=collection_name,
            embedding_function=self.embeddings,
        )

    def store(self, text: str, file_id: str) -> None:
        try:
            with self._lock:
                print(f"[DEBUG] 📄 원본 텍스트 길이: {len(text)}")
                chunks = self.text_splitter.split_text(text)
                print(f"[DEBUG] 🔪 생성된 chunk 수: {len(chunks)}")

                if not chunks:
                    print(f"[⚠️] No chunks generated for file_id={file_id}, skipping store.")
                    return

                collection_name = self._get_collection_name(file_id)
                vectorstore = self._get_vectorstore(collection_name)

                now = datetime.now(ZoneInfo("Asia/Seoul"))
                today = now.strftime('%Y-%m-%d')

                documents = [
                    Document(
                        page_content=chunk,
                        metadata={"file_id": file_id, 
                        "chunk_index": i,
                        "date": today
                        }
                    )
                    for i, chunk in enumerate(chunks)
                ]

                vectorstore.add_documents(documents)
                print(f"[✅] {len(documents)}개 문서가 vectorstore에 저장됨.")
        except Exception as e:
            print(f"[store] ❌ 벡터 저장 실패: {e}")

    def get_docs(self, file_id: str, k: int = 30) -> List[Document]:
        try:
            collection_name = self._get_collection_name(file_id)
            vectorstore = self._get_vectorstore(collection_name)
            return vectorstore.similarity_search("summary", k=k)
        except Exception as e:
            print(f"[get_docs] ❌ 유사 문서 검색 실패: {e}")
            return []

    def delete_document(self, file_id: str) -> bool:
        try:
            with self._lock:
                collection_name = self._get_collection_name(file_id)
                if self.client:
                    self.client.delete_collection(collection_name)
            return True
        except Exception as e:
            print(f"[delete_document] ❌ 문서 삭제 실패: {e}")
            return False

    def list_stored_documents(self) -> List[str]:
        try:
            if self.client:
                collections = self.client.list_collections()
                return [col.name for col in collections]
            else:
                return []
        except Exception as e:
            print(f"[list_stored_documents] ❌ 문서 목록 조회 실패: {e}")
            return []

    def cleanup_unused_vectors(self, cache) -> List[str]:
        deleted = []
        try:
            vector_ids = self.list_stored_documents()
            for fid in vector_ids:
                if not cache.get_pdf(fid):
                    self.delete_document(fid)
                    self.log_vector_deletion(fid)
                    deleted.append(fid)
        except Exception as e:
            print(f"[VectorDB.cleanup_unused_vectors] ❌ 에러: {e}")
        return deleted

    def log_vector_deletion(self, file_id: str):
        now = datetime.now(ZoneInfo("Asia/Seoul"))
        date_key = f"vector:deleted:{now.strftime('%Y-%m-%d')}"
        self.r = get_cache_db().r
        self.r.rpush(date_key, f"{file_id}|{now.isoformat()}")

    def is_chroma_alive(self) -> bool:
        try:
            if self.client:
                self.client.heartbeat()
                return True
        except:
            return False
        return False
    
    def delete_all_vectors(self) -> int:
        file_ids = self.list_stored_documents()
        deleted_count = 0
        for fid in file_ids:
            if self.delete_document(fid):
                self.log_vector_deletion(fid)
                deleted_count += 1
        return deleted_count

    def get_vectors_by_date(self, date_str: str) -> List[str]:
        matched_ids = set()
        try:
            vector_ids = self.list_stored_documents()
            for fid in vector_ids:
                try:
                    vectorstore = self._get_vectorstore(fid)
                    docs = vectorstore.similarity_search("dummy", k=1)  # 일부만 불러도 메타데이터 확인 가능
                    for doc in docs:
                        if doc.metadata.get("date") == date_str:
                            matched_ids.add(fid)
                            break
                except Exception as e:
                    print(f"[get_vectors_by_date] ⚠️ {fid} 처리 중 오류: {e}")
        except Exception as e:
            print(f"[get_vectors_by_date] ❌ 전체 조회 실패: {e}")
        return list(matched_ids)

    def get_memory_estimate(self) -> dict:
        try:
            base_path = os.getenv("CHROMA_DB_IMPL", "/chroma")  # 실제 경로로 변경
            size_bytes = self._get_directory_size(base_path)
            return {
                "base_path": base_path,
                "disk_usage_bytes": size_bytes,
                "disk_usage_mb": round(size_bytes / (1024 * 1024), 2)
            }
        except Exception as e:
            return {"error": str(e)}
    

    def _get_directory_size(self, path: str) -> int:
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                if os.path.isfile(fp):
                    total_size += os.path.getsize(fp)
        return total_size


@lru_cache(maxsize=1)
def get_vector_db() -> "VectorDB":
    try:
        return VectorDB()
    except Exception as e:
        print(f"[get_vector_db] ❌ VectorDB 초기화 실패: {e}")
        return None

