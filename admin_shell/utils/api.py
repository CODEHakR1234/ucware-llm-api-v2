
import requests

BASE_URL = "http://localhost:8000"

def get(path: str):
    try:
        return requests.get(f"{BASE_URL}{path}")
    except Exception as e:
        return f"GET 요청 실패: {e}"

def delete(path: str):
    try:
        return requests.delete(f"{BASE_URL}{path}")
    except Exception as e:
        return f"DELETE 요청 실패: {e}"

def post(path: str, data=None):
    try:
        return requests.post(f"{BASE_URL}{path}", json=data)
    except Exception as e:
        return f"POST 요청 실패: {e}"
