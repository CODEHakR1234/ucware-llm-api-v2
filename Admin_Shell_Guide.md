# 채팅 서비스 Shell 명령어 가이드

## 개요
채팅 서비스의 PDF 요약 기능을 위한 Shell 명령어 시스템입니다. Vector 데이터베이스와 Cache 시스템을 관리하고 PDF 요약 기능을 제공합니다.

## MainShell 명령어

### 1. exit
- **기능**: Shell 코드에서 빠져나오면서 종료
- **사용법**: `exit`

---

## 2. vector - Vector 데이터베이스 관리

Vector 데이터베이스에 저장된 파일들을 관리하는 명령어들입니다.

### 기본 명령어
- **back**: MainShell로 복귀
- **help**: 명령어 목록 보여주기

### 조회 명령어
- **statistics**: Vector에 저장된 file_id, 개수, Disk 메모리 사용량 확인
- **check**: Vector에 저장 여부 확인
  - 사용법: `check <file_id>`
- **list**: 특정 날짜 Vector에 저장된 파일 확인
  - 사용법: `list <date>`

### 삭제 명령어
- **cleanup-unused**: 캐시에 없는 file을 Vector에서도 수동 삭제
- **delete**: 특정 file 삭제
  - 사용법: `delete <file_id>`
- **all**: 모든 Vector 데이터를 전부 삭제

### 로그 관리
- **log**: 특정 날짜의 삭제 로그 확인
  - 사용법: `log <date>`
- **clear-log**: 특정 날짜 삭제 로그를 전부 삭제
  - 사용법: `clear-log <date>`

---

## 3. cache - 캐시 시스템 관리

캐시 시스템에 저장된 파일들을 관리하는 명령어들입니다.

### 기본 명령어
- **back**: MainShell로 복귀
- **help**: 명령어 목록 보여주기

### 조회 명령어
- **statistics**: Cache에 저장된 file_id, 개수, 메모리 사용량 확인
- **check**: Cache에 저장 여부 확인
  - 사용법: `check <file_id>`
- **list**: 특정 날짜 Cache에 저장된 파일 확인
  - 사용법: `list <date>`

### 삭제 명령어
- **cleanup**: TTL이 만료된 캐시 모든 캐시 데이터 삭제
- **delete**: 특정 file 삭제
  - 사용법: `delete <file_id>`
- **all**: 모든 캐시 데이터를 전부 삭제

### 로그 관리
- **log**: 특정 날짜의 삭제 로그 확인
  - 사용법: `log <date>`
- **clear-log**: 특정 날짜 삭제 로그를 전부 삭제
  - 사용법: `clear-log <date>`

---

## 4. system - 시스템 전체 관리

시스템 전체를 관리하는 명령어들입니다.

### 기본 명령어
- **back**: MainShell로 복귀
- **help**: 명령어 목록 보여주기

### 시스템 관리
- **all**: 모든 Cache / Vector 데이터 삭제

---

## 5. summary - PDF 요약 기능

PDF 파일을 요약하는 기능을 제공합니다.

### 사용법
```bash
summary <file_id> <pdf_url>
```

### 매개변수
- **file_id**: 파일 식별자
- **pdf_url**: PDF 파일의 URL

### 기능
- 지정된 PDF 파일을 분석하여 요약 수행
- 요약 결과를 반환

---

## 명령어 사용 예시

### Vector 관리 예시
```bash
# Vector 통계 확인
vector statistics

# 특정 파일 존재 확인
vector check file_123

# 특정 날짜 파일 목록 확인
vector list 2025-01-15

# 특정 파일 삭제
vector delete file_123
```

### Cache 관리 예시
```bash
# Cache 통계 확인
cache statistics

# TTL 만료 캐시 정리
cache cleanup

# 특정 날짜 로그 확인
cache log 2025-01-15
```

### PDF 요약 예시
```bash
# PDF 요약 실행
summary file_123 https://example.com/document.pdf
```

## 주의사항
- 모든 삭제 명령어는 신중하게 사용해야 합니다
- `all` 명령어는 모든 데이터를 삭제하므로 특히 주의가 필요합니다
- 날짜 형식은 YYYY-MM-DD 형식을 사용합니다
- file_id는 고유 식별자여야 합니다

## 아키텍처 구조
```
MainShell
├── vector (Vector Database)
├── cache (Cache System)
├── system (System Management)
└── summary (PDF Summary Service)
```

이 시스템은 효율적인 파일 관리와 PDF 요약 기능을 통해 채팅 서비스의 성능을 향상시킵니다.