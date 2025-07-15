
from fastapi import APIRouter, Depends, Query
from datetime import datetime
from app.vectordb.vector_db import get_vector_db, VectorDB
from app.cache.cache_db import get_cache_db

router = APIRouter(prefix="/vector", tags=["vector-management"])

@router.get("/statistics")
async def vector_statistics(vdb: VectorDB = Depends(get_vector_db)):
    try:
        file_ids = vdb.list_stored_documents()
        disk_info = vdb.get_memory_estimate()
        return {
            "count": len(file_ids),
            "file_ids": file_ids,
            "disk_estimate": disk_info
        }
    except Exception as e:
        return {"error": f"VectorDB 조회 중 오류: {e}"}

@router.get("/check/{file_id}")
async def check_vector_exists(file_id: str, vdb: VectorDB = Depends(get_vector_db)):
    return {
        "file_id": file_id,
        "exists": file_id in vdb.list_stored_documents()
    }

@router.delete("/cleanup-unused")
async def cleanup_unused_vectors(
    vdb: VectorDB = Depends(get_vector_db),
    cache = Depends(get_cache_db)
):
    """Redis 캐시에 없는 오래된 vector 컬렉션 삭제"""
    deleted = vdb.cleanup_unused_vectors(cache)
    return {
        "deleted_count": len(deleted),
        "deleted_file_ids": deleted
    }

@router.get("/cleanup-log")
async def get_cleanup_log(
    date: str = Query(..., description="YYYY-MM-DD 형식의 날짜"),
    cache = Depends(get_cache_db)
):
    key = f"vector:deleted:{date}"
    logs = cache.r.lrange(key, 0, -1)
    return {
        "date": date,
        "deleted_file_ids": [entry.split("|")[0] for entry in logs],
        "raw_entries": logs
    }

@router.delete("/delete/{file_id}")
async def delete_vector(
    file_id: str,
    vdb: VectorDB = Depends(get_vector_db)
):
    """특정 file_id의 벡터를 강제로 삭제"""
    success = vdb.delete_document(file_id)
    if success:
        vdb.log_vector_deletion(file_id)  # ✅ 여기 추가해줘야 로그에 찍힘
    return {
        "file_id": file_id,
        "deleted": success
    }

@router.delete("/all")
async def delete_all_vectors(vector: VectorDB = Depends(get_vector_db)):
    file_ids = vector.list_stored_documents()
    deleted_count = 0

    for fid in file_ids:
        if vector.delete_document(fid):
            vector.log_vector_deletion(fid)
            deleted_count += 1

    return {
        "message": "All vectors deleted",
        "deleted_count": deleted_count
    }

@router.delete("/cleanup-log")
async def delete_vector_log(
    date: str = Query(..., description="YYYY-MM-DD 형식의 날짜"),
    cache = Depends(get_cache_db)
):
    key = f"vector:deleted:{date}"
    deleted = cache.r.delete(key)
    return {
        "date": date,
        "deleted": bool(deleted)
    }

@router.get("/by-date")
async def get_vectors_by_date(date: str = Query(..., description="YYYY-MM-DD")):
    vdb = get_vector_db()
    try:
        file_ids = vdb.get_vectors_by_date(date)
        return {
            "date": date,
            "count": len(file_ids),
            "file_ids": file_ids
        }
    except Exception as e:
        return {"error": f"벡터 날짜별 조회 중 오류: {e}"}