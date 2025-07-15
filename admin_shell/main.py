
from utils.auth import load_users, verify_login
from vector_shell import vector_shell
from cache_shell import cache_shell
from system_shell import system_shell
from utils.print_helper import print_response
from utils.api import post

def main():
    print("🎮 AdminShell에 오신 것을 환영합니다")
    users = load_users()

    for attempt in range(3):
        if verify_login(users):
            break
        print(f"⛔ 남은 시도 횟수: {2 - attempt}")
    else:
        print("❌ 3회 실패로 종료합니다.")
        return

    # 로그인 성공 시 진입 메뉴
    while True:
        cmd = input("[MainShell] >> ").strip().lower()
        if cmd == "exit":
            print("👋 종료합니다.")
            break

        elif cmd == "vector":
            vector_shell()  # vector shell 진입!

        elif cmd == "cache":
            cache_shell()

        elif cmd == "system":
            system_shell()

        elif cmd == "summary":
            print("📄 요약 요청을 시작합니다.")
            file_id = input("file_id 입력: ").strip()
            pdf_url = input("pdf_url 입력: ").strip()
            data = {
                "file_id": file_id,
                "pdf_url": pdf_url
            }
            print_response(post("/summary", data))

        else:
            print("❓ 지원하지 않는 명령어입니다. (vector/cache/system/exit)")

if __name__ == "__main__":
    main()
