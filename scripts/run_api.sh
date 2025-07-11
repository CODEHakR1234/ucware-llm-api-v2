#!/bin/bash

# ────────────────────────────────────────────────
# [1] 포트 번호 입력 받기 (기본값: 8000)
# ────────────────────────────────────────────────
read -p "🌐 사용할 포트 번호를 입력하세요 [기본값: 8000]: " PORT
PORT=${PORT:-8000}  # 입력이 없으면 8000 사용

# ────────────────────────────────────────────────
# [2] .env 파일 로딩 (OPENAI_API_KEY 필요)
# ────────────────────────────────────────────────
if [ -f .env ]; then
  export $(grep OPENAI_API_KEY .env | xargs)
  echo "[ℹ️] .env에서 OPENAI_API_KEY를 불러왔습니다"
else
  echo "❌ .env 파일이 없습니다. 먼저 setup_env.sh를 실행해주세요."
  exit 1
fi

# ────────────────────────────────────────────────
# [3] FastAPI 서버 실행
# ────────────────────────────────────────────────
echo "[🚀] FastAPI 서버를 포트 $PORT 에서 실행 중..."
nohup uvicorn app.main:app --host 0.0.0.0 --port $PORT > fastapi.log 2>&1 &
#nohup uvicorn app.main:app --reload --host 0.0.0.0 --port $PORT > fastapi.log 2>&1 &
sleep 5

# ────────────────────────────────────────────────
# [4] 서버 기동 확인
# ────────────────────────────────────────────────
if lsof -i :$PORT | grep LISTEN; then
  echo "✅ FastAPI 서버가 포트 $PORT 에서 정상적으로 실행되었습니다."
else
  echo "❌ FastAPI 서버가 포트 $PORT 에서 실행되지 않았습니다."
  exit 1
fi

