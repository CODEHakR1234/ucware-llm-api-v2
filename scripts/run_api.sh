#!/bin/bash
# run_api.sh: OpenAI Key 입력 + FastAPI 서버 실행 (포트 8000)

echo -n "🔑 OpenAI API Key를 입력하세요: "
read -r OPENAI_API_KEY

export OPENAI_API_KEY="$OPENAI_API_KEY"
echo "[✔] OPENAI_API_KEY가 설정되었습니다"

echo "[🚀] FastAPI 서버 실행 중... (포트 8000)"
source .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

