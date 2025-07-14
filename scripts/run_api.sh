#!/bin/bash
# run_api.sh: OpenAI Key 설정 + Chroma 서버 확인 + FastAPI 서버 실행 (포트 8000)

# ───────────────────────────────
# 1. .env에서 OPENAI_API_KEY 로딩
# ───────────────────────────────
if [ -f .env ]; then
  set -o allexport
  source .env
  set +o allexport
  echo "[ℹ️] .env의 모든 환경 변수를 불러왔습니다"
else
  echo "❌ .env 파일이 없습니다. 먼저 setup_env.sh를 실행해주세요."
  exit 1
fi


# ───────────────────────────────
# 2. Chroma 서버가 살아날 때까지 대기
# ───────────────────────────────
echo "[🕓] Chroma 서버 상태 확인 중..."

MAX_RETRIES=30
RETRY_INTERVAL=2
COUNTER=0

while ! curl -s http://localhost:9000 > /dev/null; do
  ((COUNTER++))
  echo "🔁 Chroma가 아직 준비되지 않음 ($COUNTER/$MAX_RETRIES). ${RETRY_INTERVAL}초 후 재시도..."
  if [ "$COUNTER" -ge "$MAX_RETRIES" ]; then
    echo "❌ Chroma 서버가 준비되지 않아 FastAPI를 실행할 수 없습니다."
    exit 1
  fi
  sleep $RETRY_INTERVAL
done

echo "[✅] Chroma 서버 연결 성공!"

# ───────────────────────────────
# 3. FastAPI 서버 실행 (백그라운드)
# ───────────────────────────────
echo "[🚀] FastAPI 서버 실행 중... (포트 8000)"
nohup uvicorn app.main:app  --host 0.0.0.0 --port 8000 > fastapi.log 2>&1 &

echo "🎉 API 서버 실행 완료!"