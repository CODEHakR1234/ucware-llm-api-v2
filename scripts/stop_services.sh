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

# ────────────────────────────────────────────────
# [1] 사용자 입력
# ────────────────────────────────────────────────
read -p "🛑 종료할 포트 번호들을 입력하세요 (예: 8000 8001 8002): " PORTS

# ────────────────────────────────────────────────
# [2] 각 포트에 대해 종료 수행
# ────────────────────────────────────────────────
for PORT in $PORTS; do
  echo "🔍 포트 $PORT 확인 중..."
  API_PIDS=$(lsof -i :$PORT -t)

  if [ -n "$API_PIDS" ]; then
    echo "🛑 포트 $PORT의 FastAPI 서버 종료 중... (PID: $API_PIDS)"
    echo "$API_PIDS" | xargs kill
    echo "✔ 포트 $PORT 종료 완료"
  else
    echo "⚠️  포트 $PORT에서 실행 중인 FastAPI 서버가 없습니다."
  fi
done

echo "🛑 Redis 서버 종료 중..."
REDIS_PIDS=$(lsof -i :6379 -t)
if [ -n "$REDIS_PIDS" ]; then
  echo "$REDIS_PIDS" | xargs kill
  echo "✔ Redis (PID $REDIS_PIDS) 종료 완료"
else
  echo "⚠️  Redis 서버가 실행 중이지 않습니다."
fi

echo "✅ 모든 서버 종료 완료"

