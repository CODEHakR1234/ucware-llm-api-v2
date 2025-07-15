
from utils.api import get, delete
from utils.print_helper import print_response

BASE = "http://localhost:8000"

def vector_shell():
    print("📦 VectorShell에 진입했습니다. (type 'help' to list commands)")
    while True:
        cmd = input("[VectorShell] >> ").strip().lower()
        if cmd == "back":
            break

        elif cmd == "statistics":
            print_response(get("/vector/list"))

        elif cmd.startswith("check "):
            _, file_id = cmd.split(maxsplit=1)
            print_response(get(f"/vector/check/{file_id}"))

        elif cmd.startswith("list "):
            _, date = cmd.split(maxsplit=1)
            print_response(get(f"/vector/by-date?date={date}"))

        elif cmd.startswith("delete "):
            _, file_id = cmd.split(maxsplit=1)
            print_response(delete(f"/vector/delete/{file_id}"))

        elif cmd == "cleanup-unused":
            print_response(delete("/vector/cleanup-unused"))

        elif cmd.startswith("log "):
            _, date = cmd.split(maxsplit=1)
            print_response(get(f"/vector/cleanup-log?date={date}"))

        elif cmd.startswith("clear-log "):
            _, date = cmd.split(maxsplit=1)
            print_response(delete(f"/vector/cleanup-log?date={date}"))

        elif cmd == "all":
            print_response(delete("/vector/all"))

        elif cmd == "help":
            print("""📝 명령어 목록:
  statistics                   → 전체 저장된 벡터 리스트
  list <YYYY-MM-DD>           → 특정 날짜의 벡터 리스트
  check <file_id>             → 특정 벡터 존재 확인
  delete <file_id>            → 특정 벡터 삭제
  cleanup-unused              → 사용되지 않는 벡터 정리
  log <YYYY-MM-DD>            → 특정 날짜의 삭제 로그 조회
  clear-log <YYYY-MM-DD>      → 특정 날짜의 로그 삭제
  all                         → 모든 벡터 삭제
  back                        → MainShell로 돌아가기
""")
        else:
            print("❌ 알 수 없는 명령입니다. (help 입력 시 목록 표시)")
