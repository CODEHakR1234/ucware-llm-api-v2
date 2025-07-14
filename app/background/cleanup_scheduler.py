# app/background/cleanup_scheduler.py

import aiohttp
import asyncio
from datetime import datetime, timedelta
from app.vectordb.vector_db import get_vector_db
from app.cache.cache_db import get_cache_db

print("[DEBUG] cleanup_scheduler 모듈이 로딩되었습니다")

async def wait_for_chroma():
    while True:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("http://localhost:9000") as resp:
                    if resp.status == 200:
                        print("✅ Chroma 서버 연결 성공!", flush=True)
                        return
        except Exception:
            print("🕓 Chroma 서버가 아직 준비되지 않음. 재시도 중...", flush=True)
        await asyncio.sleep(1)

async def cleanup_job():
    print("🚀 cleanup_job 시작됨", flush=True)
    await wait_for_chroma()
    print("🔓 Chroma 확인 완료, 계속 진행", flush=True)

    try:
        vdb = get_vector_db()
        cache = get_cache_db()
    except Exception as e:
        print(f"[Cleanup Job] 초기화 중 Chroma 또는 Redis 연결 실패: {e}", flush=True)
        return

    # 🔥 (1) 시작 시 정리
    deleted = vdb.cleanup_unused_vectors(cache)
    if deleted:
        print(f"[Startup Cleanup] Deleted {len(deleted)} vector(s): {deleted}", flush=True)
    else:
        print(f"[Startup Cleanup] No vector deleted at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", flush=True)

    # 🔥 (2) 루프 시작
    while True:
        now = datetime.now()
        next_run = now + timedelta(minutes=5)
        delay = (next_run - now).total_seconds()
        print(f"[Auto Cleanup] Waiting {delay / 60:.2f} minutes until next cleanup...", flush=True)

        await asyncio.sleep(delay)

        # 🔥 (3) 주기적 정리 실행
        vdb = get_vector_db()
        cache = get_cache_db()
        deleted = vdb.cleanup_unused_vectors(cache)
        if deleted:
            print(f"[Auto Cleanup] Deleted {len(deleted)} vector(s): {deleted}", flush=True)
        else:
            print(f"[Auto Cleanup] No vector deleted at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", flush=True)

    # 무한 루프 없이 종료

# ✅ task 객체 반환
async def register_cleanup_task() -> asyncio.Task:
    print("[DEBUG] register_cleanup_task() 진입", flush=True)
    try:
        return asyncio.create_task(cleanup_job())
    except Exception as e:
        print(f"[register_cleanup_task] cleanup_job 실행 중 예외 발생: {e}", flush=True)
        return None
