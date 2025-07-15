#!/bin/bash
# stop_services.sh: chroma, uvicorn(FastAPI), redis-server 종료

echo "🛑 Chroma 서버 종료 중..."
CHROMA_PIDS=$(lsof -i :9000 -t)
if [ -n "$CHROMA_PIDS" ]; then
  echo "$CHROMA_PIDS" | xargs kill
  echo "✔ Chroma (PID $CHROMA_PIDS) 종료 완료"
else
  echo "⚠️  Chroma 서버가 실행 중이지 않습니다."
fi

echo "🛑 FastAPI 서버 종료 중..."
API_PIDS=$(lsof -i :8000 -t)
if [ -n "$API_PIDS" ]; then
  echo "$API_PIDS" | xargs kill
  echo "✔ FastAPI (PID $API_PIDS) 종료 완료"
else
  echo "⚠️  FastAPI 서버가 실행 중이지 않습니다."
fi

echo "🛑 Redis 서버 종료 중..."
REDIS_PIDS=$(lsof -i :6379 -t)
if [ -n "$REDIS_PIDS" ]; then
  echo "$REDIS_PIDS" | xargs kill
  echo "✔ Redis (PID $REDIS_PIDS) 종료 완료"
else
  echo "⚠️  Redis 서버가 실행 중이지 않습니다."
fi

echo "✅ 모든 서버 종료 완료"

