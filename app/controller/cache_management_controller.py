
from fastapi import APIRouter, Depends
from datetime import datetime, timedelta
from app.cache.cache_db import get_cache_db
from fastapi import Query

router = APIRouter(prefix="/cache", tags=["cache-management"])

@router.get("/statistics")
async def get_cache_statistics(cache = Depends(get_cache_db)):
    """캐시 통계 정보 조회"""
    return cache.get_statistics()

@router.get("/summaries/{date}")
async def get_summaries_by_date(
    date: str,
    cache = Depends(get_cache_db)
):
    """특정 날짜의 모든 요약본 조회"""
    try:
        date_obj = datetime.strptime(date, "%Y-%m-%d")
        summaries = cache.get_summaries_by_date(date_obj)
        return {
            "date": date,
            "count": len(summaries),
            "file_ids": list(summaries.keys())
        }
    except ValueError:
        return {"error": "Invalid date format. Use YYYY-MM-DD"}

@router.delete("/cleanup")
async def cleanup_expired(cache = Depends(get_cache_db)):
    """만료된 요약본 수동 정리"""
    cache.cleanup_expired_summaries()
    return {"message": "Cleanup completed"}

@router.delete("/summary/{file_id}")
async def delete_specific_summary(
    file_id: str,
    cache = Depends(get_cache_db)
):
    """특정 요약본 삭제"""
    success = cache.delete_pdf(file_id)
    return {
        "file_id": file_id,
        "deleted": success
    }

@router.get("/deletion-log")
async def get_cache_deletion_log(
    date: str = Query(..., description="YYYY-MM-DD 형식의 날짜"),
    cache = Depends(get_cache_db)
):
    key = f"cache:deleted:{date}"
    logs = cache.r.lrange(key, 0, -1)
    return {
        "date": date,
        "deleted_file_ids": [entry.split("|")[0] for entry in logs],
        "raw_entries": logs
    }


@router.get("/metadata/{file_id}")
async def get_cache_metadata(
    file_id: str,
    cache = Depends(get_cache_db)
):
    """특정 file_id의 메타데이터 조회"""
    key = f"pdf:metadata:{file_id}"
    metadata = cache.r.get(key)
    if metadata:
        return {
            "file_id": file_id,
            "metadata": json.loads(metadata)
        }
    else:
        return {
            "file_id": file_id,
            "metadata": None,
            "message": "Metadata not found"
        }

@router.delete("/all")
async def delete_all_cache(cache = Depends(get_cache_db)):
    deleted = cache.delete_all_summaries()
    return {
        "message": "All cache summaries deleted",
        "deleted_count": deleted
    }

@router.delete("/deletion-log")
async def delete_cache_log(
    date: str = Query(..., description="YYYY-MM-DD 형식의 날짜"),
    cache = Depends(get_cache_db)
):
    key = f"cache:deleted:{date}"
    deleted = cache.r.delete(key)
    return {
        "date": date,
        "deleted": bool(deleted)
    }