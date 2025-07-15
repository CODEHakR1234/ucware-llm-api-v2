
from fastapi import APIRouter, Depends
from app.cache.cache_db import get_cache_db
from app.vectordb.vector_db import get_vector_db

router = APIRouter(prefix="/system", tags=["system-management"])

@router.delete("/all")
async def delete_all_data(
    cache = Depends(get_cache_db),
    vector = Depends(get_vector_db)
):
    # 📌 Vector 삭제
    deleted_vectors = vector.delete_all_vectors()

    # 📌 Cache 삭제
    deleted_cache_count = cache.delete_all_summaries()

    return {
        "message": "All vector and cache data deleted",
        "deleted_vectors": deleted_vectors,
        "deleted_cache_entries": deleted_cache_count
    }
