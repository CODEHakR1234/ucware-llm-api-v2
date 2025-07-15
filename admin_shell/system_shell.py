
from utils.api import delete
from utils.print_helper import print_response

BASE = "http://localhost:8000"

def system_shell():
    while True:
        cmd = input("[SystemShell] >> ").strip().lower()
        if cmd == "back":
            break

        elif cmd == "all":
            confirm = input("⚠️ 정말 모든 데이터를 삭제하시겠습니까? (yes/no): ").strip().lower()
            if confirm == "yes":
                print_response(delete("/system/all"))
            else:
                print("✅ 취소되었습니다.")

        elif cmd == "help":
            print("""📝 명령어 목록:
  all       → 벡터 + 캐시 + 메타데이터 전체 삭제
  back      → MainShell로 복귀
""")
        else:
            print("❌ 알 수 없는 명령입니다. (help 입력 시 목록 표시)")
