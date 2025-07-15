
import json
import getpass
import os

def load_users(filepath: str = "admin_shell/utils/users.json") -> list:
    if not os.path.exists(filepath):
        return []
    with open(filepath, "r") as f:
        return json.load(f)

def verify_login(users: list) -> bool:
    user_id = input("Enter Admin ID: ").strip()
    user_pw = getpass.getpass("Enter Password: ").strip()

    for user in users:
        if user["id"] == user_id and user["password"] == user_pw:
            print("✅ 로그인 성공")
            return True

    print("❌ 로그인 실패: ID 또는 비밀번호가 일치하지 않습니다.")
    return False
