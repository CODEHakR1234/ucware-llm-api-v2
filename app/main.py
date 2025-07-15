
# app/main.py
import asyncio
from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.background.cleanup_scheduler import register_cleanup_task
from app.controller import (
    pdf_summary_controller,
    chat_summary_controller,
    cache_management_controller,
    vector_management_controller,
    system_management_controller
)
print("[DEBUG] main.py 시작됨", flush=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("[DEBUG] main.py 시작됨", flush=True)
    task = None
    try:
        from app.background.cleanup_scheduler import cleanup_job
        task = asyncio.create_task(cleanup_job())  # 🔥 직접 task 등록
        print("[LIFESPAN] 백그라운드 작업 등록 완료", flush=True)
    except Exception as e:
        print(f"[LIFESPAN] 백그라운드 작업 등록 중 오류: {e}", flush=True)
    yield
    if task:
        task.cancel()
        print("[LIFESPAN] 종료 시 백그라운드 작업 취소 완료", flush=True)



app = FastAPI(title="Multi-Summary API", lifespan=lifespan)

app.include_router(pdf_summary_controller.router)
app.include_router(chat_summary_controller.router)
app.include_router(cache_management_controller.router)
app.include_router(vector_management_controller.router)
app.include_router(system_management_controller.router)
