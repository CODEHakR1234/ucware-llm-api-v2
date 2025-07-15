from datetime import datetime

def log_command(user, shell, command):
    with open("admin_shell/admin.log", "a") as f:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"[{now}] ({user}) [{shell}] >> {command}\n")
