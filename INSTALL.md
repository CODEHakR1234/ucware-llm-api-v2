# INSTALL.md

## 🛠️ 설치 가이드: ucware-llm-api-v1

이 문서는 `ucware-llm-api-v1` 프로젝트를 설치하고 실행하기 위한 전체 환경 설정 방법을 안내합니다.

---

## 📌 1. 시스템 요구 사항

- Ubuntu 20.04+ 또는 호환 리눅스 배포판
- Python 3.10 이상
- Redis 서버
- PDF 및 OCR 처리를 위한 도구들 (tesseract)

---

## 📦 2. 시스템 패키지 설치

```bash
sudo apt update
sudo apt install -y \
    redis-server \
```


### 🔍 Redis 상태 확인 및 실행
```bash
sudo systemctl enable redis
sudo systemctl start redis
sudo systemctl status redis
```

---

## 🐍 3. Python 가상환경 설정 (권장)

```bash
python3 -m venv .venv
source .venv/bin/activate
```

---

## 📚 4. Python 패키지 설치

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

---

## 🚀 5. 서버 실행

### 🌐 PDF 및 채팅 요약 API 서버 실행
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

> 기본적으로 `8000` 포트를 사용하며, 필요 시 설정 변경 가능

---

## 🧪 6. 테스트 및 확인 (실제 테스트 기준 반영)

### ✅ 채팅 요약 API 테스트
```bash
curl -X POST http://localhost:8000/chat-summary \
  -H "Content-Type: application/json" \
  -d '{
        "chats": [
          {
            "chat_id": "c1",
            "plaintext": "안녕하세요.",
            "sender": "user",
            "timestamp": "2024-07-01T12:00:00"
          },
          {
            "chat_id": "c2",
            "plaintext": "논문 요약 부탁드려요.",
            "sender": "user",
            "timestamp": "2024-07-01T12:01:00"
          }
        ]
      }'
```
응답 예시:
```json
{"summary":"User greets and asks for a summary of a paper."}
```

### ✅ PDF 요약 API 테스트 (요약 결과 캐싱 포함)
```bash
curl -X POST http://localhost:8000/summary \
  -H "Content-Type: application/json" \
  -d '{
        "file_id": "paper-01",
        "pdf_url": "https://arxiv.org/pdf/1706.03762.pdf"
      }'
```
응답 예시:
```json
{"file_id":"paper-01","summary":"The paper ...","cached":true}
```

```bash
curl -X POST http://localhost:8000/summary \
  -H "Content-Type: application/json" \
  -d '{
        "file_id": "paper-02",
        "pdf_url": "https://www.csun.edu/sites/default/files/pdf_scanned_ocr.pdf"
      }'
```
응답 예시:
```json
{"file_id":"paper-02","summary":"CSUN provides free ...","cached":false}
```

---

## 📎 참고사항

- `redis-server`는 캐시 시스템의 백엔드로 사용됩니다.

---

## ✅ 요약 체크리스트

- [x] 시스템 패키지 설치 (apt)
- [x] Python 의존성 설치 (pip)
- [x] Redis 실행 확인
- [x] FastAPI 서버 실행
- [x] 채팅 요약 및 PDF 요약 API 정상 응답 확인

