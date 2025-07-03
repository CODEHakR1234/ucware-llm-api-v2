#!/bin/bash
# run_api.sh: OpenAI Key 설정 + FastAPI 서버 실행 (포트 8000)

# 이미 환경변수 설정되어 있는지 확인
if [[ -z "$OPENAI_API_KEY" ]]; then
  echo -n "🔑 OpenAI API Key를 입력하세요: "
  read -r OPENAI_API_KEY
  export OPENAI_API_KEY="$OPENAI_API_KEY"
  echo "[✔] OPENAI_API_KEY가 설정되었습니다"
else
  echo "[ℹ️] OPENAI_API_KEY가 이미 설정되어 있습니다"
fi

# FastAPI 서버 실행
echo "[🚀] FastAPI 서버 실행 중... (포트 8000)"
source .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

