
import json
from pprint import pprint

def print_response(res):
    if isinstance(res, str):
        print(res)
    elif hasattr(res, "json"):
        try:
            pprint(res.json())
        except Exception:
            print(res.text)
    else:
        print(res)
