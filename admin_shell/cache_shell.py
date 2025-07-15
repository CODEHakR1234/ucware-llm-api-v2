
from utils.api import get, delete
from utils.print_helper import print_response

BASE = "http://localhost:8000"

def cache_shell():
    print("💾 CacheShell에 진입했습니다. (type 'help' to list commands)")
    while True:
        cmd = input("[CacheShell] >> ").strip().lower()
        if cmd == "back":
            break

        elif cmd == "statistics":
            print_response(get("/cache/statistics"))

        elif cmd.startswith("check "):
            _, file_id = cmd.split(maxsplit=1)
            print_response(get(f"/cache/check/{file_id}"))

        elif cmd.startswith("list "):
            _, date = cmd.split(maxsplit=1)
            print_response(get(f"/cache/summaries/{date}"))

        elif cmd == "cleanup":
            print_response(delete("/cache/cleanup"))

        elif cmd.startswith("delete "):
            _, file_id = cmd.split(maxsplit=1)
            print_response(delete(f"/cache/summary/{file_id}"))

        elif cmd == "all":
            print_response(delete("/cache/all"))

        elif cmd.startswith("log "):
            _, date = cmd.split(maxsplit=1)
            print_response(get(f"/cache/deletion-log?date={date}"))

        elif cmd.startswith("clear-log "):
            _, date = cmd.split(maxsplit=1)
            print_response(delete(f"/cache/deletion-log?date={date}"))

        elif cmd == "help":
            print("""📝 명령어 목록:
  statistics                  → 캐시 통계 조회
  check <file_id>            → 특정 캐시 존재 확인
  list <YYYY-MM-DD>          → 특정 날짜 저장 캐시 조회
  delete <file_id>           → 특정 캐시 삭제
  cleanup                    → TTL 만료된 캐시 정리
  all                        → 전체 캐시 삭제
  log <YYYY-MM-DD>           → 삭제 로그 조회
  clear-log <YYYY-MM-DD>     → 삭제 로그 제거
  back                       → MainShell로 복귀
""")
        else:
            print("❌ 알 수 없는 명령입니다. (help 입력 시 목록 표시)")
