import aiohttp
import asyncio
from datetime import datetime, timedelta
from app.vectordb.vector_db import get_vector_db
from app.cache.cache_db import get_cache_db
from zoneinfo import ZoneInfo 

print("[DEBUG] cleanup_scheduler 모듈이 로딩되었습니다", flush=True)

# ────────────────────────────────
# 1. Chroma가 뜰 때까지 대기
# ────────────────────────────────
async def wait_for_chroma():
    while True:
        try:
            print("[DEBUG] 🕓 Chroma 연결 시도 중...", flush=True)
            async with aiohttp.ClientSession() as session:
                async with session.get("http://localhost:9000/docs") as resp:
                    print(f"[DEBUG] 📡 Chroma 응답 코드: {resp.status}", flush=True)
                    if resp.status == 200:
                        print("[DEBUG] ✅ Chroma 서버 연결 성공!", flush=True)
                        return
        except Exception as e:
            print(f"[DEBUG] ❌ Chroma 연결 예외 발생: {e}", flush=True)
        await asyncio.sleep(1)

# ────────────────────────────────
# 2. 매일 새벽 3시 자동 정리 잡
# ────────────────────────────────
async def cleanup_job():
    print("[DEBUG] 🚀 cleanup_job 시작됨", flush=True)
    await wait_for_chroma()
    print("[DEBUG] 🔓 Chroma 확인 완료, 계속 진행", flush=True)

    while True:
        now = datetime.now(ZoneInfo("Asia/Seoul"))
        tomorrow_3am = (now + timedelta(days=1)).replace(hour=3, minute=0, second=0, microsecond=0)
        wait_sec = (tomorrow_3am - now).total_seconds()
        print(f"[DEBUG] ⏳ 다음 정리까지 대기: {int(wait_sec)}초 (예정 시각: {tomorrow_3am})", flush=True)

        await asyncio.sleep(wait_sec)

        try:
            print("[DEBUG] 🧪 정리 전 연결 확인 중...", flush=True)
            vdb = get_vector_db()
            cache = get_cache_db()

            # 디버깅: 현재 vector 목록 및 Redis 키 출력
            vector_ids = vdb.list_stored_documents()
            print(f"[DEBUG] 📦 현재 VectorDB에 저장된 file_id 수: {len(vector_ids)}", flush=True)
            print(f"[DEBUG] 📦 VectorDB file_ids: {vector_ids}", flush=True)

            used_ids = cache.get_all_file_ids()
            print(f"[DEBUG] 📌 Redis에 남아 있는 file_id 수: {len(used_ids)}", flush=True)
            print(f"[DEBUG] 📌 Redis file_ids: {used_ids}", flush=True)

            deleted = vdb.cleanup_unused_vectors(cache)
            print(f"[Cleanup @03:00] ✅ Deleted {len(deleted)} vector(s): {deleted}", flush=True)
        except Exception as e:
            print(f"[Cleanup @03:00] ❌ 예외 발생: {e}", flush=True)

# ────────────────────────────────
# 3. FastAPI lifespan에서 호출할 task 등록 함수
# ────────────────────────────────
async def register_cleanup_task() -> asyncio.Task:
    print("[DEBUG] register_cleanup_task() 진입", flush=True)
    try:
        return asyncio.create_task(cleanup_job())
    except Exception as e:
        print(f"[register_cleanup_task] cleanup_job 실행 중 예외 발생: {e}", flush=True)
        return None
