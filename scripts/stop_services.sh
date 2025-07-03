#!/bin/bash
# stop_services.sh: chroma, uvicorn(FastAPI), redis-server 종료

echo "🛑 Chroma 서버 종료 중..."
CHROMA_PID=$(lsof -i :9000 -t)
if [ -n "$CHROMA_PID" ]; then
  kill "$CHROMA_PID"
  echo "✔ Chroma (PID $CHROMA_PID) 종료 완료"
else
  echo "⚠️  Chroma 서버가 실행 중이지 않습니다."
fi

echo "🛑 FastAPI 서버 종료 중..."
API_PID=$(lsof -i :8000 -t)
if [ -n "$API_PID" ]; then
  kill "$API_PID"
  echo "✔ FastAPI (PID $API_PID) 종료 완료"
else
  echo "⚠️  FastAPI 서버가 실행 중이지 않습니다."
fi

echo "🛑 Redis 서버 종료 중..."
REDIS_PID=$(lsof -i :6379 -t)
if [ -n "$REDIS_PID" ]; then
  kill "$REDIS_PID"
  echo "✔ Redis (PID $REDIS_PID) 종료 완료"
else
  echo "⚠️  Redis 서버가 실행 중이지 않습니다."
fi

echo "✅ 모든 서버 종료 완료"

