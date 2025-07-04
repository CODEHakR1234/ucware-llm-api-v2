#!/bin/bash
# setup_env.sh: Python 패키지 설치 + .env 생성

echo "[1] 시스템 패키지 설치"
sudo apt update
sudo apt install -y redis-server 

echo "[2] Python 가상환경 생성 및 활성화"
python3 -m venv .venv
source .venv/bin/activate

echo "[3] pip 패키지 설치"
pip install --upgrade pip
pip install -r requirements.txt

echo -n "🔑 OpenAI API Key를 입력하세요: "
read -r OPENAI_API_KEY

echo "[4] .env 파일 생성"
cat > .env <<EOF
CHROMA_HOST=localhost
CHROMA_PORT=9000
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_TTL=604800
OPENAI_API_KEY=$OPENAI_API_KEY
EOF

echo "[✔] .env 생성 완료"
